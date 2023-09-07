from aiogram import F, Router
from aiogram.types import Message
from aiogram.dispatcher.filters import Command

import os

from dotenv.main import load_dotenv

import psycopg2
from psycopg2 import Error

router = Router()
load_dotenv()


@router.message(Command(commands=['start']))
async def cmd_start(message: Message):
    try:
        connection = psycopg2.connect(
                host=os.environ['HOST'],
                user=os.environ['USER'],
                password=os.environ['PASSWORD'],
                database=os.environ['DB_NAME'],
            )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users
                VALUES (%s, Null);
                """, (message.chat.id,)
            )
        await message.answer('Вы зарегистрированы!')
    except (Exception, Error) as er:
        print('Something went wrong with PostgreSQL in Spam.py!', er)
        if type(er) == psycopg2.errors.UniqueViolation:
            await message.answer('Вы зарегистрированы!')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.message(F.text == 'run')
async def spam_true(message: Message):
    try:
        connection = psycopg2.connect(
                host=os.environ['HOST'],
                user=os.environ['USER'],
                password=os.environ['PASSWORD'],
                database=os.environ['DB_NAME'],
            )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET spam = True
                WHERE id = %s;
                """, (message.chat.id,)
            )
        await message.answer('Возобновление рассылки')
    except (Exception, Error) as er:
        print('Something went wrong with PostgreSQL in Spam.py!', er)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.message(F.text == 'stop')
async def spam_false(message: Message):
    try:
        connection = psycopg2.connect(
                host=os.environ['HOST'],
                user=os.environ['USER'],
                password=os.environ['PASSWORD'],
                database=os.environ['DB_NAME'],
            )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET spam = False
                WHERE id = %s;
                """, (message.chat.id,)
            )
        await message.answer('Рассылка прекращена!')
    except (Exception, Error) as er:
        print('Something went wrong with PostgreSQL in Spam.py!', er)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
