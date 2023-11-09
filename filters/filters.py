from typing import Any
from aiogram.dispatcher.filters import BaseFilter
from aiogram.types import Message


class VkLink(BaseFilter):
    """Проверяет является ли сообщение от пользователя ссылкой на
    сообщество вк"""

    async def __call__(self, message: Message) -> bool:
        if not message.entities:
            return False
        for item in message.entities:
            if item.type == 'url':
                link = item.extract(message.text)
                return ('vk.com' in link or 'vk.cc' in link)


class NotFirstTime(BaseFilter):
    """Фильтр проверяет есть ли пользователь в базе данных.
    Чтобы попасть в базу данных нужно вводить команду /start"""

    async def __call__(self, message: Message, **kwargs) -> bool:
        cursor = kwargs['kwargs']['cursor']
        cursor.execute(
            """
            SELECT id
                FROM public.users
                WHERE id = %s
            """, (message.chat.id, )
        )
        fetch = cursor.fetchone()
        if fetch:
            return True
        else:
            await message.answer(
                text=r'Нажмите команду /start чтобы зарегистрироваться!'
            )
            return False


class AdminCommands(BaseFilter):
    """Filter allows specific commands only to Admin Users"""

    async def __call__(self, message: Message, **kwargs) -> bool:
        return message.chat.id == 5245286301
