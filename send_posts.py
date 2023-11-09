import json
import shutil
import os
import asyncio
import logging

from aiogram import Bot, types
from aiogram.utils.markdown import hlink

from vk_operations.get_wall import get_wall, get_many_content


async def timed_send(bot: Bot, cursor, logging: logging):
    try:
        cursor.execute(
            """
            DELETE FROM public.publics
                WHERE subscribers = '{}';
            """
        )
    except Exception as ex:
        logging.error(
            msg='Невозможно получить доступ к базе данных!'
                ' Сообщества без подписчиков не удалены',
            exc_info=True
        )

    try:
        cursor.execute(
            """
            SELECT publics.group
                FROM publics
            """
        )
    except Exception as ex:
        logging.exception(
            msg='Невозможно получить доступ к базе данных!'
                ' Данные сообществ не получены',
            exc_info=True
        )
        return

    groups = [item[0] for item in cursor.fetchall()]
    for group in groups:
        posts = get_wall(group, logging)
        if posts:
            cursor.execute(
                """
                UPDATE public.publics SET posts = %s
                    WHERE publics.group = %s
                """,
                (json.dumps(posts), group)
            )
        await asyncio.sleep(0.5)

    try:
        cursor.execute(
            """
            SELECT "group", posts, old_posts, name, subscribers, link
                FROM public.publics
            """
        )
        data = cursor.fetchall()
    except Exception as ex:
        logging.exception(
            msg='Данные сообществ не получены!'
        )
        return

    for public in data:
        names = [
            'group_id',
            'new_posts',
            'old_posts',
            'group_name',
            'subscribers_list',
            'link_to_group'
        ]

        public_dict = {}
        for value, name in zip(public, names):
            public_dict[name] = value

        to_send_keys = public_dict['new_posts'].keys()
        if public_dict['old_posts']:
            to_send_keys = to_send_keys - public_dict['old_posts'].keys()
        if not to_send_keys:
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

        send = [public_dict['new_posts'][key] for key in sorted(to_send_keys)]
        for id in id_list:
            for post_index, values in enumerate(send):
                text_value = ''

                if not values['text']:
                    text_value = hlink(public_dict['group_name'], public_dict['link_to_group'])
                elif len(str(values['text'])) > 950:
                    text_value = str(values['text'])[:950] + '...' \
                        + f'\n{hlink(public_dict["group_name"], public_dict["link_to_group"])}'
                else:
                    text_value = str(values['text']) \
                        + f'\n{hlink(public_dict["group_name"], public_dict["link_to_group"])}'

                await asyncio.sleep(0.5)

                if len(values['media']) <= 2:
                    if values['media']:
                        if values['media'][1] == 'photo':
                            try:
                                await bot.send_photo(
                                    chat_id=id,
                                    photo=values['media'][0],
                                    caption=text_value,
                                    parse_mode='HTML'
                                )
                            except Exception as ex:
                                logging.error(
                                    msg='Unable to send single Photo via Telegram!'
                                        f' Group_id = {public_dict["group_id"]}'
                                        f' Message_id = {send[post_index]}',
                                        exc_info=True
                                )
                        else:
                            try:
                                await bot.send_video(
                                    chat_id=id,
                                    video=types.FSInputFile(f'videos/{values["media"][0]}'),
                                    caption=text_value,
                                    parse_mode='HTML'
                                )
                            except Exception as ex:
                                logging.error(
                                    msg='Unable to send single Video via Telegram!'
                                        f' Group_id = {public_dict["group_id"]}'
                                        f' Message_id = {send[post_index]}',
                                        exc_info=True
                                )
                    else:
                        try:
                            await bot.send_message(
                                chat_id=id,
                                text=text_value,
                                parse_mode='HTML',
                            )
                        except Exception as ex:
                            logging.error(
                                msg='Unable to send Text message via Telegram!'
                                    f' Group_id = {public_dict["group_id"]}'
                                    f' Message_id = {send[post_index]}',
                                    exc_info=True
                            )
                else:
                    media = get_many_content(
                        media=values['media'], text=text_value
                    )
                    try:
                        await bot.send_media_group(chat_id=id, media=media)
                    except Exception as ex:
                        logging.error(
                            msg='Unable to send media_group via Telegram!'
                                f' Group_id = {public_dict["group_id"]}'
                                f' Message_id = {send[post_index]}',
                                exc_info=True
                        )

        cursor.execute(
            """
            UPDATE public.publics
                SET old_posts = %s
                WHERE publics.group = %s
            """, (json.dumps(public_dict['new_posts']), public_dict['group_id'])
        )
