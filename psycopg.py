import os

import psycopg2
import json
from pprint import pprint
from dotenv.main import load_dotenv

load_dotenv()

dic = {'171778': {'photos': ['https://sun9-21.userapi.com/impg/x1f1ks0bJQBSq_Hwn1m8heC0eXDQHjQVgnLqaQ/I2aQfkfhE-U.jpg?size=376x256&quality=95&sign=fa333118ec7d923137492120c03ef3a7&c_uniq_tag=iTmBeARwfqNVeRYUvuykFoJaOqy8-5YHB6_1zyejduw&type=album'],
          'text': 'Друзья, наконец-то дошли руки создать телегу нашего '      
                  'паблика, там будут поститься все новые посты из вк, а так '
                  'же разбавляться годными хорошо забытыми старыми, +доп '    
                  'контент. Возможно кому-то будет удобнее там, '
                  'подписывайтесь!\n'
                  'https://t.me/repou3'},
 '186446': {'photos': ['https://sun7-21.userapi.com/impg/Mt6bb4GzzuXX7ycpS0aCnb9PcEzBemQsFb01BA/a2l2qtOrWIU.jpg?size=682x665&quality=95&sign=b3f63ee0c6d599f29d79ec9b24629510&c_uniq_tag=ZXdwLdxUNsGKrR6x3bMOjgL4SlpZFd8WdcHH2gsuXzY&type=album'],
          'text': ''},
 '186577': {'photos': ['https://sun7-23.userapi.com/impg/x8GXs8gTR7WDLQNYUPEoaPEznd5igAyoqD_w_Q/Afh2pBOZyHI.jpg?size=600x598&quality=95&sign=2f5f4a70a71b98f961afce554e0f1c6b&c_uniq_tag=oodoFBxXMzc1btsuB4sEj5bEfAg43kZHqyCZpwUsRlw&type=album'],
          'text': ''},
 '186678': {'photos': ['https://sun7-21.userapi.com/impg/ZOM-kXJ_MnaiO9NneTeJwcu4gVlkLlM2dXdimA/AwZ3MPyAw5M.jpg?size=634x604&quality=95&sign=cc5c3f12808059e6e84744e0e0fccb67&c_uniq_tag=a17XIb90OZ2cTXsfGjVivoY5peyt0UWKOjl10jE_yTQ&type=album'],
          'text': ''},
 '186729': {'photos': ['https://sun7-19.userapi.com/impg/oCTfXT7hM8Kw_PkGSCS3zzbCpglTOicw7Ux5EA/WQmmfJm2Yug.jpg?size=583x519&quality=95&sign=ea20638c324bc37d2a271c29f984bd79&c_uniq_tag=GVPmgA21eJ6VByUpuq3mGdswXruOQMLKvfMo4mo6reI&type=album'],
          'text': ''}}
dic = json.dumps(dic)
dic2 = json.dumps({
    '171778': {'photos': ['https://sun9-21.userapi.com/impg/x1f1ks0bJQBSq_Hwn1m8heC0eXDQHjQVgnLqaQ/I2aQfkfhE-U.jpg?size=376x256&quality=95&sign=fa333118ec7d923137492120c03ef3a7&c_uniq_tag=iTmBeARwfqNVeRYUvuykFoJaOqy8-5YHB6_1zyejduw&type=album'],
          'text': 'Друзья, наконец-то дошли руки создать телегу нашего '      
                  'паблика, там будут поститься все новые посты из вк, а так '
                  'же разбавляться годными хорошо забытыми старыми, +доп '    
                  'контент. Возможно кому-то будет удобнее там, '
                  'подписывайтесь!\n'
                  'https://t.me/repou3'},
    }
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
        id = 218892320
        cursor.execute(
                """
                SELECT publics.group FROM public.publics WHERE publics.group = %s
                """, ([id])
            )
        existance = cursor.fetchone()
        print(existance)
        # print('Created')
        # cursor.execute(
        #     """INSERT INTO users VALUES
        #     (5245286301, '{334424,121568313,29534144,218892324,29544671}')
        #     """
        # )
        # print('Succes!')
        # cursor.execute(
        #     """INSERT INTO public.publics VALUES (121568313, %s, %s, ARRAY ['5245286301'])""", (dic, dic2)
        # )
        # cursor.execute(
        #     """SELECT posts FROM publics"""
        # )
        # data = cursor.fetchone()
        # cursor.execute(
        #     """SELECT old_posts FROM publics"""
        # )
        # old_data = cursor.fetchone()
        # old_data_keys = list(old_data[0].keys())
        # groups = data[0]
        # for key in groups.keys():
        #     if key not in old_data_keys:
        #         pprint(groups[key])
        # print(list(groups.keys()))

except Exception as _ex:
    print('[INFO] Ошибка в работе с PostgreSQL', _ex)
finally:
    if connection:
        connection.close()
        print('Connection closed!')
