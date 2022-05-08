import os
import requests
from urllib.parse import urlencode


class YandexDiskWork:

    def __init__(self):
        self.yandex_token = os.environ['YANDEX_TOKEN']

    def upload_file(self, loadfile, savefile, replace=False):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                   'Authorization': f'OAuth {self.yandex_token}'}
        res = requests.get(f'{url}/upload?path={savefile}&overwrite={replace}', headers=headers).json()
        with open(loadfile, 'rb') as f:
            requests.put(res['href'], files={'file': f})

    def download_file(self, path, file_name):
        base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
        public_key = path
        final_url = base_url + urlencode(dict(public_key=public_key))
        response = requests.get(final_url)
        download_url = response.json()['href']

        download_response = requests.get(download_url)
        with open('./src/' + file_name, 'wb') as f:
            f.write(download_response.content)
