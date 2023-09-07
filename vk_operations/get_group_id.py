import os

from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

load_dotenv()


headers = {
    'user-agent': os.getenv('user-agent'),
}
url_list = [
    'https://vk.com/onepiece',
    'https://vk.com/repouiii',
    'https://vk.com/lentach',
    'https://vk.com/public218892324',
    'https://vk.com/zloyshkolnik'
]


def get_group_id(url):
    r = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')
    scripts = soup.find_all('meta', property="og:url")
    print(list(scripts))
    address = list(str(scripts[0]).split('\"')[1].split('vk.com/')[-1])
    id = ''
    for symbol in address:
        if symbol.isdigit():
            id = id + str(symbol)
    return int(id)


if __name__ == '__main__':
    print([get_group_id(url) for url in url_list])
