import os
from pprint import pprint

from aiogram import types
from dotenv import load_dotenv
import requests

load_dotenv()

access_token = os.getenv('access_token')


def get_max_size_url(sizes):
    height, width = 0, 0
    url = ''
    for picture in sizes:
        if picture['height'] >= height or picture['width'] >= width:
            height = picture['height']
            width = picture['width']
            url = picture['url']
    return url


def get_content(attachments, text):
    for index, media in enumerate(attachments):
        if media.get('type') != 'photo':
            del attachments[index]
    if not attachments:
        return ''
    elif len(attachments) == 1:
        return [get_max_size_url(
            attachments[0].get('photo', '').get('sizes', '')
        ), ]
    media_list = []
    for media in attachments:
        media_list.append(types.InputMediaPhoto(
            type='photo',
            media=get_max_size_url(media.get('photo', '').get('sizes')),
            caption=text
            ))
        text = None
    return media_list


def get_wall(group_id: int) -> dict:
    posts = requests.get(
        'https://api.vk.com/method/wall.get',
        params={
            'access_token': access_token,
            'owner_id': -group_id,
            'count': '5',
            'v': '5.131',
            'extended': 'True'
        }
    ).json()
    new_posts = {}
    for post in posts['response']['items']:
        new_posts[post['id']] = {
            'text': post['text'],
            'photos': get_content(post.get('attachments', []), post['text']),
        }
    return new_posts


if __name__ == "__main__":
    pprint(get_wall(334424))
