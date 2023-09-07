import os

import psycopg2
import json
from pprint import pprint
from dotenv.main import load_dotenv

load_dotenv()

dic = {
    '1605002': {
        'photos': ['https://sun7-24.userapi.com/impg/D5Vk-hlvsoXShHsL3NexEM4suDPaH5mhda2Cog/ve8z-faKLF8.jpg?size=1100x1600&quality=95&sign=40f3d9db06ffb56c5741374e1c57872a&c_uniq_tag=OF6qBe3-VKYD6_TqSEcgEBkVT-ezDJ3wo03l41RZ3L8&type=album'],
        'text': 'Вышла 1091 глава манги One Piece: "Сентомару"\n'
                'Скачать: https://vk.cc/cqx8ST\n'
                'На следующей неделе главы не будет!'},
    '1605880': {
        'photos': ['https://sun7-24.userapi.com/impg/Bb7GI-6vW9pSEonLJ8MoC5FEnHWV22uWbY0uYw/2y5Nt_-bgHs.jpg?size=1280x1811&quality=96&sign=1f102219df2dabcf7f57a10989ae2dc5&c_uniq_tag=nY4E3Y3czpyemqofrJpsLK63eUEk00AoIG1UKih3RmA&type=album'],
        'text': '#фанарт@onepiece \n \nАвтор: mskrysta-art'},
}
dic = json.dumps(dic)
dic2 = json.dumps({
    '1605002': {
        'photos': ['https://sun7-24.userapi.com/impg/D5Vk-hlvsoXShHsL3NexEM4suDPaH5mhda2Cog/ve8z-faKLF8.jpg?size=1100x1600&quality=95&sign=40f3d9db06ffb56c5741374e1c57872a&c_uniq_tag=OF6qBe3-VKYD6_TqSEcgEBkVT-ezDJ3wo03l41RZ3L8&type=album'],
        'text': 'Вышла 1091 глава манги One Piece: "Сентомару"\n'
                'Скачать: https://vk.cc/cqx8ST\n'
                'На следующей неделе главы не будет!'},}
    )

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
            """CREATE TABLE IF NOT EXISTS users(
                id bigint NOT NULL,
                groups text[]
            );"""
        )
        print('Created')
        # cursor.execute(
        #     """INSERT INTO users VALUES
        #     (5245286301, '{334424,121568313,29534144,218892324,29544671}')
        #     """
        # )
        # print('Succes!')
        # cursor.execute(
        #     """INSERT INTO public.publics("group", posts, old_posts) VALUES (
        #     334424, %s, %s)""", (dic, dic2)
        # )
        cursor.execute(
            """SELECT posts FROM publics"""
        )
        data = cursor.fetchone()
        cursor.execute(
            """SELECT old_posts FROM publics"""
        )
        old_data = cursor.fetchone()
        old_data_keys = list(old_data[0].keys())
        groups = data[0]
        for key in groups.keys():
            if key not in old_data_keys:
                pprint(groups[key])
        print(list(groups.keys()))

except Exception as _ex:
    print('[INFO] Ошибка в работе с PostgreSQL', _ex)
finally:
    if connection:
        connection.close()
        print('Connection closed!')
