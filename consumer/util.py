import os
import uuid

from PIL import Image

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