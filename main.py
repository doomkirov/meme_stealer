import os

import asyncio
import logging
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from send_posts import timed_send

from handlers import spam

# from commands import start_commands
# from videos import direct_send, youtube_link_send

load_dotenv()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.getenv('bot_token'))


scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
scheduler.add_job(
        timed_send,
        trigger='interval',
        seconds=2,
        kwargs={'bot': bot},
        id='1',
    )


async def main():
    dp = Dispatcher()

    scheduler.start()

    dp.include_router(spam.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
