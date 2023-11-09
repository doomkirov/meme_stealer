from aiogram import Bot, F, Router, types
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hlink
# from aiogram.dispatcher.fsm.state import StatesGroup, State
# from aiogram.dispatcher.fsm.context import FSMContext

import asyncio

from send_posts import timed_send
from filters.filters import VkLink, NotFirstTime, AdminCommands
from vk_operations.get_group_id import get_group_id
from vk_operations.get_wall import get_group_name, check_privacy


router = Router()


# class WaitingState(StatesGroup):
#     waiting_state = State()


@router.message(Command(commands=['start']))
async def cmd_start(message: Message, **kwargs):
    """Пользователь вводит команду /start,
    после чего его id попадает в базу данных."""
    cursor = kwargs['kwargs']['cursor']
    cursor.execute(
        """
        INSERT INTO users
            VALUES (%s, true, null)
            ON CONFLICT (id) DO NOTHING;
        """, (message.chat.id,)
    )
    await message.answer(
        'Привет! Этот бот может брать все записи из'
        ' НЕприватных сообществ ВКонтакте и пересылать в этот чат!'
        ' Больше не нужно заходить в вечно лагающий ВК чтобы'
        ' проверить свои любимые сообщества на обновления!'
        '\n\nЧтобы бот начал работу, пришлите ему ссылку на любое'
        ' \n!НЕприватное\nсообщество и спустя немного времени вы начнёте'
        ' получать записи этого и всех своих других сообществ!'
        '\nНапример: (https://vk.com/public218892324)'
        '\n\nКоличество сообществ не ограничено, однако стоит помнить - бот не пересылает музыку'
        '\n\nСписок доступных команд Вы всегда можете найти по кнопке Меню слева от поля ввода текста'
    )


@router.message(NotFirstTime(), Command(commands=['run']))
async def spam_true(message: Message, **kwargs):
    """Пользовательская команда /run, меняет значение
    spam в базе данных на True, благодаря чему пользователь
    включается в рассылку данных."""
    cursor = kwargs['kwargs']['cursor']
    cursor.execute(
        """
        UPDATE users
            SET spam = True
            WHERE id = %s;
        """, (message.chat.id,)
    )
    await message.answer('Возобновление рассылки')


@router.message(NotFirstTime(), Command(commands=['stop']))
async def spam_false(message: Message, **kwargs):
    """Пользовательская команда /stop, меняет значение
    spam в базе данных на False, благодаря чему пользователь
    перестаёт получать данные по рассылке, сохраняя свои подписки."""
    cursor = kwargs['kwargs']['cursor']
    cursor.execute(
        """
        UPDATE users
            SET spam = False
            WHERE id = %s;
        """, (message.chat.id,)
    )
    await message.answer('Рассылка прекращена!')


@router.message(NotFirstTime(), VkLink())
async def vk_link_handled(message: Message, **kwargs):
    """Если зарегистрированный пользователь отправил ссылку на сообщество vk,
    сообщество в свою очередь не является приватным, то это сообщество
    добавляется в базу данных, пользователь становится его подписчиком."""
    cursor = kwargs['kwargs']['cursor']
    link = ''
    for item in message.entities:
        if item.type == 'url':
            link = item.extract(message.text)
    group_id = get_group_id(link)
    if not check_privacy(group_id=group_id):
        await message.answer(
            'Невозможно получить доступ к данному сообществу.'
            ' Возможно оно является приватным или не существует.'
        )
        return
    cursor.execute(
        """
        SELECT publics.group
            FROM public.publics
            WHERE publics.group = %s
        """, ([group_id])
    )
    existance = cursor.fetchone()
    group_name = get_group_name(group_id)
    if not existance:
        cursor.execute(
            """
            INSERT INTO public.publics("group", subscribers, name, link)
                VALUES (%s, %s, %s, %s)
            """, (group_id, [str(message.chat.id)], group_name, link)
        )
    else:
        cursor.execute(
            """
            UPDATE publics
                SET subscribers = array_append(subscribers, %s)
                WHERE publics.group = %s
            """, (str(message.chat.id), group_id)
        )
    await message.answer(
        text=f'Вы подписались на обновления сообщества {group_name}'
    )
    cursor.execute(
        """
        UPDATE users
            SET "groups" = array_append("groups", %s)
            WHERE id = %s
        """, (str(group_id), message.chat.id)
    )


@router.message(NotFirstTime(), Command(commands=['list']))
async def list_of_subs(message: Message, **kwargs):
    """Выводит все подписки пользователя (команда /list)."""
    cursor = kwargs['kwargs']['cursor']
    cursor.execute(
        """
        SELECT name, link
            FROM public.publics
            WHERE %s = ANY (publics.subscribers)
        """, (str(message.chat.id),)
    )
    subs = cursor.fetchall()
    text = ''
    for data in subs:
        text += f'{hlink(data[0], data[1])}\n'
    if not text:
        text = 'Вы не подписаны ни на одно сообщество!'
    await message.answer(
        text=text,
        parse_mode='HTML',
        disable_web_page_preview=True
    )


@router.message(NotFirstTime(), Command(commands=['follow']))
async def follow_command(message: Message):
    """Сообщает пользователю о том как подписаться на сообщество
    (команда /follow)."""
    await message.answer(
        text='Просто пришлите мне ссылку на '
             'сообщество, на которое вы хотите подписаться, и я всё сделаю!',
    )


@router.message(NotFirstTime(), Command(commands=['unfollow']))
async def unfollow_command(message: Message, **kwargs):
    """Команда /unfollow выводит InlineKeyboard, состоящую из
    подписок пользователя. По нажатию кнопки соответствующее сообщество будет
    удалено из подписок пользователя, в списке подписчиков сообщества
    пользователь так же будет удалён."""
    cursor = kwargs['kwargs']['cursor']
    cursor.execute(
        """
        SELECT name
            FROM public.publics
            WHERE %s = ANY (publics.subscribers)
        """, (str(message.chat.id),)
    )
    subs = cursor.fetchall()
    builder = InlineKeyboardBuilder()
    for name in subs:
        builder.add(InlineKeyboardButton(
            text=name[0],
            callback_data=name[0]
        ))
    builder.add(InlineKeyboardButton(
        text='Отмена',
        callback_data='cancel_unfollow_cmd'
    ))
    builder.adjust(3)
    await message.answer(
        text='Выберите сообщество от которого хотите отписаться',
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'cancel_unfollow_cmd')
async def cancel_unfollow_cmd(callback: CallbackQuery):
    """Нажатие InlineKeyboard 'Отмена' команды /unfollow."""
    await callback.message.edit_reply_markup(None)
    await callback.message.answer(
        text='Команда отменена!'
    )
    await callback.answer()


@router.callback_query()
async def get_pub_to_unfollow(callback: CallbackQuery, **kwargs):
    """Отписка от выбранного пользователем в InlineKeyboard сообщества."""
    await callback.message.edit_reply_markup(None)
    cursor = kwargs['kwargs']['cursor']
    cursor.execute(
        """
        SELECT "group", link
            FROM public.publics
            WHERE name = %s
        """, (callback.data,)
    )
    group = cursor.fetchone()
    cursor.execute(
        """
        UPDATE users
            SET "groups" = array_remove("groups", %s)
            WHERE id = %s
        """, (str(group[0]), callback.message.chat.id)
    )
    cursor.execute(
        """
        UPDATE public.publics
            SET subscribers=array_remove(subscribers, %s)
            WHERE name=%s;
        """, (str(callback.message.chat.id), callback.data)
    )
    await callback.message.answer(
        text='Вы успешно отписались от сообщества '
             f'{hlink(callback.data, group[1])}',
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(AdminCommands(), F.text.lower() == 'обновить')
async def refresh_posts(message: Message, bot: Bot, **kwargs):
    await message.answer(text='Команда обработана! Обновляемся...')
    logging = kwargs['kwargs']['logging']
    cursor = kwargs['kwargs']['cursor']
    await timed_send(bot=bot, cursor=cursor, logging=logging)


# @router.message()
# async def video_id(message: Message, bot: Bot, **kwargs):
#     list = [
#         types.InputMediaPhoto(
#             type='photo',
#             media='https://sun9-25.userapi.com/impg/xKlYR3fJj9D9MQ6gMeEuyyIUFynTQuGmKIK74w/6uup-URjfng.jpg?size=800x575&quality=96&sign=4199a45e060a0b00724241190a60df98&type=album',
#             caption='Hello',
#             parse_mode='HTML'
#         ),
#         types.InputMediaVideo(
#             type='video',
#             media=types.FSInputFile(f'videos/video2.mp4'),
#             caption=None,
#             parse_mode='HTML'
#         ),
#         types.InputMediaVideo(
#             type='video',
#             media=types.FSInputFile(f'videos/video1.mp4'),
#             caption=None,
#             parse_mode='HTML'
#         )
#     ]
#     info = await message.answer_media_group(
#         media=list,
#     )
#     for inff1 in info:
#         if inff1.video:
#             print(inff1.video.file_id)

# Тестирование сообщений с задержкой через State. Рабочий код:

# @router.message(WaitingState.waiting_state)
# async def unwaiting(message: Message, state: FSMContext):
#     await message.answer(f'Спасибо, что ответил! Ты {message.text}')
    # await state.clear()


# @router.message(F.text.lower() == 'привет')
# async def waiting(message: Message, state: FSMContext):
#     await message.answer(text="Отправь мне свое имя")
#     await state.set_state(WaitingState.waiting_state.state) # Ваш state
    # await asyncio.sleep(5) # 5 сек спим
    # if await state.get_state() == 'WaitingState:waiting_state':
    #     await message.answer(text='Я не дождался ответа :-(')
    #     await state.clear()