import logging
import torch
import torch.nn.functional as F
import io
import psycopg2
import boto3
import os
import matplotlib.pyplot as plt
from PIL import Image
import uuid
from ts.torch_handler.base_handler import BaseHandler
from facenet_pytorch import MTCNN

class face_detection(BaseHandler):
    """
    Custom handler for pytorch serve. This handler supports batch requests.
    For a deep description of all method check out the doc:
    https://pytorch.org/serve/custom_service.html
    """
    def __init__(self):
        self.model = None
        self.initialized = False

    def initialize(self, context):

        properties = context.system_properties
        model_dir = properties.get("model_dir")
        model_pth_path = os.path.join(model_dir, "mtcnn.pth")
        self.model = torch.load(model_pth_path)
        self.model.eval()
        self.initialized = True

    def preprocess(self, req):
        img = req[0].get("data")

        if img is None:
            img = req[0].get("body")
        
        image = Image.open(io.BytesIO(img))

        fpath = str(uuid.uuid4())

        return image, fpath

    def inference(self, image):
        """
        Given the data from .preprocess, perform inference using the model.
        We return the predicted label for each image.
        """

        boxes, _ = self.model.detect(image)
        return boxes

    def postprocess(self, boxes, image, path):

        w, h = image.size
        image_list = []
        a = 0

        for box in zip(boxes):
            if int(box[0][0]) < 0: #left
                box[0][0] = 0
            if int(box[0][1]) < 0: #top
                box[0][1] = 0
            if int(box[0][2]) > w: #right
                box[0][2] = w
            if int(box[0][3]) > h: #bottom
                box[0][3] = h

            area = (int(box[0][0]), int(box[0][1]), int(box[0][2]), int(box[0][3]))
            cropped = image.crop(area)
            image_list.append(cropped)
            
            img_name = path + str(a) +'.jpg'
            directory = 'face_images'

            if os.path.exists(directory) == False:
                os.mkdir(directory)

            cropped.save(f"{directory}/{img_name}")
            a += 1

        return image_list

    def saveImage(self, images, path):
        if len(images) != 0:

            s3 = boto3.resource('s3',
                                endpoint_url='https://s3.us-west-1.wasabisys.com/',
                                aws_access_key_id='BOA82RVHP6PXW22ZJM61',
                                aws_secret_access_key='YE9OnzcbgNrQvwHXCww8PZSd4oj5tCrmzil1Kink'
                                )

            boto_test_bucket = s3.Bucket('sgg-dev-ai')

            object_folder = 'manual-book-project/'

            con = psycopg2.connect(
                host="localhost",
                database="mydb",
                user="postgres",
                password="fotoyu"
            )

            cur = con.cursor()

            cur.execute(
                "select id, user_id, image_link from images order by id DESC Limit 1")

            rows = cur.fetchall()

            raw_image_id = 0
            for r in rows:
                raw_image_id = r[0]

            result = []
            a = 0
            for filename in os.listdir('face_images'):
                image_path = os.path.join('face_images', filename)
                image_name = 'face_images/' + filename
                dest = object_folder + image_name

                boto_test_bucket.upload_file(image_path, dest)

                cur.execute("insert into cropped_images (image_id, cropped_image_link) values (%s, %s)",
                            (raw_image_id, dest))

                con.commit()
                
                os.remove(image_path)
                a+=1

            result.append({'Total face found' : a})
            con.close()

            if len(images) == 1:
                f, axarr = plt.subplots(1,a)
                for i in range(len(images)):
                    axarr.imshow(images[i])
            else:
                f, axarr = plt.subplots(1,a)
                for i in range(len(images)):
                    axarr[i].imshow(images[i])
                
            plt.show()

        else:
            result.append({'Total face found' : 0})
        return result