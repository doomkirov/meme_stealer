import os
import logging
import time

import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import psycopg2

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from send_posts import timed_send

from handlers import spam

# from commands import start_commands
# from videos import direct_send, youtube_link_send

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    filename='meme_stealer.log',
    format="%(asctime)s %(levelname)s %(message)s",
    encoding='utf-8',
)
bot = Bot(token=os.getenv('bot_token'))
dp = Dispatcher()

dp.include_router(spam.router)
scheduler = AsyncIOScheduler(timezone='Europe/Moscow')


def attempt():
    while True:
        try:
            connection = psycopg2.connect(
                    host=os.environ['HOST'],
                    user=os.environ['USER'],
                    password=os.environ['PASSWORD'],
                    database=os.environ['DB_NAME'],
                )
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id bigint NOT NULL,
                    spam boolean NOT NULL DEFAULT false,
                    groups text[]
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS publics (
                    "group" bigint PRIMARY KEY NOT NULL,
                    posts json,
                    old_posts json,
                    name text,
                    subscribers text[],
                    link text
                );
                """
            )
            scheduler.add_job(
                timed_send,
                trigger='interval',
                # seconds=5,
                minutes=15,
                kwargs={'bot': bot, 'cursor': cursor, 'logging': logging},
                id='1',
            )

            async def main():
                scheduler.start()
                await timed_send(bot, cursor, logging)

                await bot.delete_webhook(drop_pending_updates=True)
                try:
                    await dp.start_polling(bot, kwargs={'cursor': cursor, 'logging': logging})
                except Exception as ex:
                    logging.warning(
                        msg=f'dp.POLLING: Error! {ex}',
                        exc_info=True
                    )

            asyncio.run(main())

        except (Exception, psycopg2.Error) as er:
            logging.error('Something went wrong!', er, stack_info=True)

        finally:
            if cursor:
                cursor.close()
            logging.info('Cursor closed!')
            if connection:
                connection.close()
            logging.info('Connection closed!')
            scheduler.remove_job(job_id='1')
            logging.info('Retrying in 15...')
            asyncio.get_event_loop().close()
            break


if __name__ == "__main__":
    while True:
        attempt()
        # time.sleep(15)
        break
