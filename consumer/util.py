import os
import uuid

from PIL import Image
import requests
import urllib
import posixpath
import json

from requests.exceptions import RequestException


class Save():
    directory = ''
    image_files = []

    @staticmethod
    def setup(directory):
        os.makedirs(directory, exist_ok=True)
        
        Save.directory = directory

    @staticmethod
    def saveImage(image):

        guid = str(uuid.uuid4())

        fname = f'{guid}.jpg'
        
        image_path = os.path.join(Save.directory, fname)

        with open(image_path, "wb") as f:
            image.save(f, format='jpeg')

        Save.image_files.append(image_path)

        return fname, image_path

class Infer():

    @staticmethod
    def get_predict(img_bytes):
        ts_url = 'http://host.docker.internal:8080'

        try:
            relative_url = posixpath.join('predictions', 'mymodel')
            predict_url = urllib.parse.urljoin(ts_url, relative_url)

            response = requests.post(predict_url, files={'data': img_bytes})
            result = json.loads(response.content)              

            return result
        except RequestException as e:
            print('failed')
            exit()