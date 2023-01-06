
import requests
from pprint import pprint
from datetime import datetime
import time
from progress.bar import IncrementalBar
# pip freeze > requirements.txt


class ClassVK:
    def __init__(self, token, owner_id, version='5.131'):
        self.token = token
        self.version_api = version
        self.id = owner_id
        self.url = 'https://api.vk.com/method/photos.get'
        self.params = {
            'access_token': self.token,
            'v': self.version_api
        }

    def get_photos(self, owner_id=None, album_key='saved', count=1000):
        """Method to get .json of all pictures in album.
        Parameters:
            owner_id - id user from which need to download photos. If 'None' uses self id
            album_key - name of album from which need to download photos
            count - quantity of photo to download. Default is 1000"""
        owner_id = self.id if not owner_id else owner_id
        params = {'owner_id': owner_id,
                  'album_id': album_key,
                  'extended': 1,
                  'photo_sizes': 1,
                  'count': count}
        photos = requests.get(url=self.url, params={**self.params, **params})
        # print(photos.status_code)
        # print(photos)
        return photos.json()

    def user(self):
        """Method for get user information"""
        params = {
            'user_ids': self.id
        }
        user_profile = requests.get(url='https://api.vk.com/method/users.get', params={**self.params, **params})
        print(user_profile.status_code)
        return user_profile.json()

    def large_photos(self, owner_id=None, album_key='saved', count=1000):
        """Gets the large photos list. Parameters look at the method 'get_photos'"""
        photos = self.get_photos(owner_id=owner_id, album_key=album_key, count=count)
        large_photos = []
        progress_vk = IncrementalBar('Getting pictures:', max=min(count, len(photos['response']['items'])))
        for img in photos['response']['items']:
            dimensions = img['sizes']
            biggest = max([size['height'] * size['width'] for size in dimensions])
            for size in dimensions:
                if size['height'] * size['width'] == biggest:
                    img_params = {
                        'date': img['date'],
                        'likes': img['likes'],
                        'square_pixels': biggest,
                        **size
                    }
                    large_photos.append(img_params)
                    progress_vk.next()
                    time.sleep(0.01)
                    break
        # pprint(large_photos)
        progress_vk.finish()
        return large_photos

    def sort_size(self, photos):
        sort_list = sorted([file['square_pixels'] for file in photos], reverse=True)
        return sort_list


class YaUploader:
    def __init__(self, token, url='https://cloud-api.yandex.net/v1/disk/resources'):
        self.token = token
        self.url = url

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.token}'
        }

    def _get_link(self, file_upload_path):
        upload_url = self.url + '/upload'
        params = {
            'path': file_upload_path,
            'overwrite': 'True'
        }
        headers = self.get_headers()
        link = requests.get(url=upload_url, params=params, headers=headers)
        # print(link)
        return link.json()

    def upload(self, file_upload_path, file_list, quantity=5):
        """Метод загружает файлы по списку file_list на яндекс диск"""
        create_folder = requests.put(url=f'{self.url}?path={file_upload_path}', headers=self.get_headers())
        cnt = 0
        sort_list = sorted([file['square_pixels'] for file in file_list], reverse=True)
        to_json_file = []
        progress_bar = IncrementalBar('Uploading to Yandex.Disk:', max=min(quantity, len(file_list)))
        for file in file_list:
            if file['square_pixels'] in sort_list[:quantity]:
                likes_count = file['likes']['count']
                if [likes['likes']['count'] for likes in file_list].count(likes_count) > 1:
                    date_load = str(datetime.utcfromtimestamp(file['date'])).replace(' ', '_').replace(':', '-')
                    file_name = str(file['likes']['count']) + '_' + date_load + '.jpg'
                else:
                    file_name = str(file['likes']['count']) + '.jpg'
                # print(file_upload_path)
                # print(file_name)
                folder_path = file_upload_path + file_name
                # print(folder_path)
                href = self._get_link(folder_path)['href']
                response = requests.put(href, data=requests.get(file['url']))
                response.raise_for_status()
                if response.status_code == 201:
                    # print(f'Success upload: {file}')
                    cnt += 1
                    progress_bar.next()
                    writing = {
                        'file_name': f'{file_name}',
                        'size': f'{file["type"]}'
                        }
                    to_json_file.append(writing)
                if cnt == quantity:
                    break
        progress_bar.finish()
        return to_json_file


# Input data from user #
user_id = '12637305'
# files 'VK.txt' and 'Yandex.txt' contains tokens for VK application and Yandex.disk must be in project folder
album_name = 'profile'

if __name__ == '__main__':
    with open('VK.txt', 'r', encoding='utf8') as file_token:
        token_vk = file_token.read()
    with open('Yandex.txt', 'r', encoding='utf8') as file_token_ya:
        token_yandex = file_token_ya.read()
    vk = ClassVK(token=token_vk, owner_id=user_id)
    # photos = vk.get_photos()
    # print(len(photos['response']['items']))
    # profile = vk.user()
    # pprint(profile)
    # print(vk.token)
    photos_upload = vk.large_photos(album_key=album_name)
    largest_photo = vk.sort_size(photos_upload)
    # print('largest_photo =', largest_photo)
    # print('largest_photo =', len(largest_photo))
    url_ya = 'https://cloud-api.yandex.net/v1/disk/resources'
    path_to_file = 'VK_Downloads/'
    uploader = YaUploader(token=token_yandex, url=url_ya)
    logs = uploader.upload(file_upload_path=path_to_file, file_list=photos_upload, quantity=5)
    pprint(logs)
    with open(file='logs.json', mode='w', encoding='utf8') as result_logs:
        result_logs.write(str(logs))
        # result_logs.writelines(logs)
