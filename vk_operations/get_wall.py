import os
from pprint import pprint
import logging
import json

from aiogram import types
from dotenv import load_dotenv
import requests
from pytube import YouTube

from .download_video import get_video, get_youtube_url

load_dotenv()

access_token = os.getenv('access_token')


def get_group_name(id: int) -> str:
    group = requests.get(
        'https://api.vk.com/method/groups.getById',
        params={
            'access_token': access_token,
            'group_id': id,
            'v': '5.131',
        }
    ).json()
    return group['response'][0]['name']


def get_max_size_url(sizes: list) -> str:
    height, width = 0, 0
    url = ''
    for picture in sizes:
        if picture['height'] * picture['width'] > width * height:
            height = picture['height']
            width = picture['width']
            url = picture['url']
    return url


def get_content(attachments: list, logging: logging, group_id: int) -> list[str]:
    index = 0
    for _ in range(len(attachments)):
        if attachments[index].get('type') != 'photo' and attachments[index].get('type') != 'video':
            del attachments[index]
        else:
            index += 1

    if not attachments:
        return []
    elif len(attachments) == 1:
        if attachments[0].get('type') == 'photo':
            r_lst = [get_max_size_url(
                attachments[0].get('photo', '').get('sizes', '')
            ), 'photo']
            if r_lst[0]:
                r_lst[0] = r_lst[0][0:8] + r_lst[0][8:].replace('/', '//')
            return r_lst
        else:
            if attachments[0].get('video')['duration'] < 600:
                daat = attachments[0].get('video')
                owner_id, video_id = str(abs(daat['owner_id'])), str(daat['id'])
                if daat.get('type', '') == 'short_video':
                    link = 'https://vk.com/clips-' + owner_id + '?z=clip-' + owner_id + '_' + video_id
                else:
                    link = 'https://vk.com/video-' + owner_id + '_' + video_id
                filename = owner_id + '_' + video_id
                if not os.path.exists(f'videos/{filename}.mp4'):
                    try:
                        get_video(video_url=link, filename=filename)
                    except:
                        try:
                            YouTube(
                                get_youtube_url(link), use_oauth=True
                                ).streams.filter(type='video', res=['480p', '360p', '240p', '144p']).get_highest_resolution().download(
                                    output_path='videos/',
                                    filename=f'{filename}.mp4'
                                )
                        except:
                            logging.error(
                                msg='get_wall: Video download eror!'
                                    f'\nVideo link - {link}'
                                    f' Group - {get_group_name(group_id)}',
                                exc_info=False
                            )
                            return []
                return [filename + '.mp4', 'video']
            return []

    media_list = []
    for media in attachments:
        if media.get('type') == 'photo':
            r_str = get_max_size_url(
                media.get('photo', '').get('sizes', '')
            )
            if r_str:
                r_str = r_str[0:8] + r_str[8:].replace('/', '//')
            media_list.append(r_str)
            media_list.append('photo')
        else:
            if media.get('video')['duration'] < 600:
                daat = media.get('video')
                owner_id, video_id = str(abs(daat['owner_id'])), str(daat['id'])
                if daat.get('type', '') == 'short_video':
                    link = 'https://vk.com/clips-' + owner_id + '?z=clip-' + owner_id + '_' + video_id
                else:
                    link = 'https://vk.com/video-' + owner_id + '_' + video_id
                filename = owner_id + '_' + video_id
                if not os.path.exists(f'videos/{filename}.mp4'):
                    try:
                        get_video(video_url=link, filename=filename)
                        media_list.append(filename + '.mp4')
                        media_list.append('video')
                    except:
                        try:
                            YouTube(
                                get_youtube_url(link), use_oauth=True
                                ).streams.filter(type='video', res=['480p', '360p', '240p', '144p']).get_highest_resolution().download(
                                    output_path='videos/',
                                    filename=f'{filename}.mp4'
                                )
                            media_list.append(filename + '.mp4')
                            media_list.append('video')
                        except:
                            logging.error(
                                msg='get_wall: Video download eror!'
                                    f'\nVideo link - {link}'
                                    f' Group - {get_group_name(group_id)}',
                                exc_info=False
                            )
    return media_list


def get_many_content(media: list[str], text: str) -> list[types.InputMediaPhoto, types.InputMediaVideo]:
    media_list = []
    for index in range(0, len(media), 2):
        if media[index+1] == 'photo':
            media_list.append(types.InputMediaPhoto(
                type='photo',
                media=media[index],
                caption=text,
                parse_mode='HTML'
                ))
            text = None
        else:
            media_list.append(types.InputMediaVideo(
                type='video',
                media=types.FSInputFile(f'videos/{media[index]}'),
                caption=text,
                parse_mode='HTML'
            ))
            text = None
    return media_list


def check_privacy(group_id: int) -> bool:
    response = requests.get(
        'https://api.vk.com/method/wall.get',
        params={
            'access_token': access_token,
            'owner_id': -group_id,
            'count': '5',
            'v': '5.131',
            'extended': 'True'
        }
    ).json()
    if response.get('error', ''):
        return False
    elif response.get('response', '').get('groups', ''):
        return bool(response.get('response', '').get('groups', ''))
    return False


def get_wall(group_id: int, logging: logging) -> dict:
    try:
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
    except Exception as ex:
        logging.error(
            msg='Не удалось выполнить request VK api!'
                f' Группа: {group_id}',
            exc_info=True
        )

    new_posts = {}
    try:
        if posts['response']['items']:
            pass
    except Exception as ex:
        logging.error(
            msg='VK api вернул неожиданный ответ!'
                f' Ключи posts: {posts.keys()}'
                f' Группа: {group_id}'
        )
        return {}

    # check if item is an ad
    for index, item in enumerate(posts['response']['items']):
        if item.get('marked_as_ads', 1) == 1:
            del posts['response']['items'][index]

    # with open('vk_response.json', 'w', encoding='utf-8') as file:
    #     json.dump(obj=posts, fp=file, ensure_ascii=False, indent=4)
    #     return


    for post in posts['response']['items']:
        if 'copy_history' in post.keys():
            post = post['copy_history'][0]
        new_posts[str(post['id'])] = {
            'text': post['text'],
            'media': get_content(post.get('attachments', []), logging, group_id),
        }
        if (not new_posts[str(post['id'])]['media'] and
           not new_posts[str(post['id'])]['text']):
            del new_posts[str(post['id'])]
    return new_posts


if __name__ == "__main__":
    pprint(get_wall(218892324, logging=logging))
    # pprint(res['1606564']['media'])
    # pprint(get_group_name(40740411))
    # 218892324 mine
    # 334424 onepiece
    # 40740411 kirov mamo4ki
    # 76746437 listen program
    # 114437208 uralmem
    # 32041317 9gag
    # 121568313 heroesIII
    # 222657873 faith check
    # 6365467 private hent
    # 107402181 acrobat
