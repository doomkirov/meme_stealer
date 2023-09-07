import os
from aiogram import Bot

from dotenv.main import load_dotenv

import psycopg2
from psycopg2 import Error

load_dotenv()


async def timed_send(bot: Bot):
    try:
        connection = psycopg2.connect(
            host=os.environ['HOST'],
            user=os.environ['USER'],
            password=os.environ['PASSWORD'],
            database=os.environ['DB_NAME'],
        )
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM users WHERE spam = True;
                """
            )
            id_list = cursor.fetchall()
            print(id_list)
            if id_list:
                for id in id_list[0]:
                    for i in range(3):
                        await bot.send_message(chat_id=int(id), text='Hello!')
    except (Exception, Error) as er:
        print('Something went wrong with PostgreSQL in send_posts.py!', er)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
