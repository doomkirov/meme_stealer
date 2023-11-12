import json
import asyncio
import logging

from aiogram import Bot, types
from aiogram.utils.markdown import hlink

from vk_operations.get_wall import get_wall, get_many_content


async def send_single_media(
        bot: Bot, text_value: str,
        public_dict: dict, cursor,
        send: list, post_index: int,
        values: dict, logging: logging,
        id: int
        ):
    if values['media'][1] == 'photo':
        try:
            await bot.send_photo(
                chat_id=id,
                photo=values['media'][0],
                caption=text_value,
                parse_mode='HTML'
            )
        except Exception:
            logging.error(
                msg='Unable to send single Photo via Telegram!'
                    f' Group_id = {public_dict["group_id"]}'
                    f' Message_id = {send[post_index]}',
                    exc_info=True
            )
    else:
        try:
            video_link = 'https://vk.com/video-' + values['media'][0][:-4]
            cursor.execute(
                """
                SELECT telegram_file_id
                    FROM sended_videos
                    WHERE video_link = %s
                """, (video_link, )
            )
            telegram_file_id = cursor.fetchone()
            if telegram_file_id:
                await bot.send_video(
                    chat_id=id,
                    video=telegram_file_id[0],
                    caption=text_value,
                    parse_mode='HTML'
                )
            else:
                video_data = await bot.send_video(
                    chat_id=id,
                    video=types.FSInputFile(f'videos/{values["media"][0]}'),
                    caption=text_value,
                    parse_mode='HTML'
                )
                telegram_file_id = video_data.video.file_id
                cursor.execute(
                    """
                    INSERT INTO sended_videos(video_link, telegram_file_id)
                        VALUES (%s, %s)
                    """, (video_link, telegram_file_id)
                )
        except Exception:
            logging.error(
                msg='Unable to send single Video via Telegram!'
                    f' Group_id = {public_dict["group_id"]}'
                    f' Message_id = {send[post_index]}',
                    exc_info=True
            )


async def send_text_message(
        bot: Bot,
        text_value: str,
        public_dict: dict,
        send: list,
        post_index: int,
        logging: logging,
        id: int
        ):
    try:
        await bot.send_message(
            chat_id=id,
            text=text_value,
            parse_mode='HTML',
        )
    except Exception:
        logging.error(
            msg='Unable to send Text message via Telegram!'
                f' Group_id = {public_dict["group_id"]}'
                f' Message_id = {send[post_index]}',
                exc_info=True
        )


async def send_media_group(
        bot: Bot,
        id: int,
        media: list,
        public_dict: dict,
        send: list,
        post_index: int,
        cursor
        ):
    try:
        info = await bot.send_media_group(chat_id=id, media=media)
        data_list = []
        for file in info:
            if file.video:
                data_list.append(
                    ('https://vk.com/video-' + file.video.file_name[:-4], file.video.file_id, )
                )
        if data_list:
            data_str = ','.join(cursor.mogrify("%s", (x, )) for x in data_list)
            cursor.execute('INSERT INTO public.sended_videos(video_link, telegram_file_id) VALUES ' + data_str)

    except Exception:
        logging.error(
            msg='Unable to send media_group via Telegram!'
                f' Group_id = {public_dict["group_id"]}'
                f' Message_id = {send[post_index]}',
                exc_info=True
        )


async def timed_send(bot: Bot, cursor, logging: logging):
    try:
        cursor.execute(
            """
            DELETE FROM public.publics
                WHERE subscribers = '{}';
            """
        )
    except Exception:
        logging.error(
            msg='Невозможно получить доступ к базе данных!'
                ' Сообщества без подписчиков не удалены',
            exc_info=True
        )

    try:
        cursor.execute(
            """
            SELECT "group", old_posts, name, subscribers, link
                FROM public.publics
            """
        )
        data = cursor.fetchall()
    except Exception:
        logging.exception(
            msg='Данные сообществ не получены!'
        )
        return

    for public in data:
        names = [
            'group_id',
            'old_posts',
            'group_name',
            'subscribers_list',
            'link_to_group'
        ]

        public_dict = {}
        for value, name in zip(public, names):
            public_dict[name] = value
        await asyncio.sleep(1)

        get_wall_data = get_wall(
            group_id=public_dict['group_id'],
            logging=logging,
            old_ids=public_dict['old_posts'] if public_dict['old_posts'] else []
        )
        if not get_wall_data:
            await asyncio.sleep(5)
            continue
        posts = get_wall_data[0]
        new_old_ids = get_wall_data[1]

        if not posts:
            continue

        subscribers = [int(ids) for ids in public_dict['subscribers_list']]
        cursor.execute(
            """
            SELECT id FROM users
                WHERE id = ANY (%s)
                AND spam = True;
            """, (subscribers,)
        )
        id_list = cursor.fetchall()
        if id_list:
            id_list = [id[0] for id in id_list]
        else:
            continue

        send = [posts[key] for key in sorted(posts.keys())]
        for id in id_list:
            for post_index, values in enumerate(send):
                text_value = ''

                if not values['text']:
                    text_value = hlink(
                        public_dict['group_name'],
                        public_dict['link_to_group']
                    )
                elif len(str(values['text'])) > 950:
                    text_value = str(values['text'])[:950] + '...' \
                        + f'\n{hlink(public_dict["group_name"], public_dict["link_to_group"])}'
                else:
                    text_value = str(values['text']) \
                        + f'\n{hlink(public_dict["group_name"], public_dict["link_to_group"])}'

                if len(values['media']) <= 2:
                    if values['media']:
                        await send_single_media(
                            bot=bot, text_value=text_value, public_dict=public_dict,
                            cursor=cursor, send=send, post_index=post_index,
                            values=values, logging=logging, id=id
                        )
                    else:
                        await send_text_message(
                            bot=bot, text_value=text_value, public_dict=public_dict,
                            send=send, post_index=post_index, logging=logging,
                            id=id
                        )
                else:
                    await send_media_group(
                        bot=bot, id=id,
                        media=get_many_content(
                            media=values['media'], text=text_value, cursor=cursor
                        ),
                        public_dict=public_dict, send=send,
                        post_index=post_index, cursor=cursor
                    )

        cursor.execute(
            """
            UPDATE public.publics
                SET old_posts = %s
                WHERE publics.group = %s
            """, (new_old_ids, public_dict['group_id'])
        )
