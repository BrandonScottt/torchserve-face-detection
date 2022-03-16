import pika
import ast
import requests
import uuid
import psycopg2
import boto3
import sys
import os
from PIL import Image
import matplotlib.pyplot as plt

class MetaClass(type):

    _instance = {}

    def __call__(cls, *args, **kwargs):
        """ Singelton Design Pattern  """

        if cls not in cls._instance:
            cls._instance[cls] = super(
                MetaClass, cls).__call__(*args, **kwargs)
            return cls._instance[cls]


class RabbitMqServerConfigure(metaclass=MetaClass):

    def __init__(self, host='localhost', queue='image'):
        """ Server initialization   """

        self.host = host
        self.queue = queue


class rabbitmqServer():

    def __init__(self, server):
        """
        :param server: Object of class RabbitMqServerConfigure
        """

        self.server = server
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.server.host))
        self._channel = self._connection.channel()
        self._tem = self._channel.queue_declare(queue=self.server.queue)
        print("Server started waiting for Messages...")

    @staticmethod
    def callback(ch, method, properties, body):

        Payload = body.decode("utf-8")
        Payload = ast.literal_eval(Payload)

        image_path = str(uuid.uuid4()) + '.jpg'

        with open(image_path, "wb") as f:
            f.write(Payload)

        print("Image received")

        '''
        cloud connection
        '''
        s3 = boto3.resource('s3',
                            endpoint_url='https://s3.us-west-1.wasabisys.com/',
                            aws_access_key_id='BOA82RVHP6PXW22ZJM61',
                            aws_secret_access_key='YE9OnzcbgNrQvwHXCww8PZSd4oj5tCrmzil1Kink'
                            )

        boto_test_bucket = s3.Bucket('sgg-dev-ai')

        object_folder = 'manual-book-project'

        dest = object_folder + "/" + image_path

        boto_test_bucket.upload_file(image_path, dest)
        print('Image sent to cloud!')

        '''
        database connection
        '''

        connection = psycopg2.connect(
            host="localhost",
            database="mydb",
            user="postgres",
            password="fotoyu"
        )

        cur = connection.cursor()

        '''
        insert and select in users table
        '''
        cur.execute("insert into users DEFAULT values")

        cur.execute("select id from users order by id DESC Limit 1")
        rows = cur.fetchall()

        for r in rows:
            newest_id = r[0]

        '''
        insert and select in images table
        '''
        object_folder = 'manual-book-project'
        dest = object_folder + '/' + image_path

        cur.execute("insert into images (user_id, image_link) values (%s, %s)",
                    (newest_id, dest))

        connection.commit()

        connection.close()
        
        print('Image sent to database!')
        res = requests.post("http://localhost:8080/predictions/mymodel" , files={'data': open(image_path, 'rb')})

        print('Detection complete!')

        '''
        show images
        '''

        connection = psycopg2.connect(
            host="localhost",
            database="mydb",
            user="postgres",
            password="fotoyu"
        )

        cur = connection.cursor()

        cur.execute("select id from users order by id DESC Limit 1")

        rows = cur.fetchall()

        newest_id = 0
        for r in rows:
            newest_id = r[0]

        cur.execute("SELECT i.image_link, c.cropped_image_link FROM users u JOIN images i on i.user_id = u.id JOIN cropped_images c on c.image_id = i.id WHERE u.id = %s", (newest_id, ))

        res = cur.fetchall()

        face_list = []
        for r1 in res:
            raw_img = r1[0]
            face_list.append(r1[1])

        connection.close()

        s3 = boto3.resource('s3',
            endpoint_url = 'https://s3.us-west-1.wasabisys.com/',
            aws_access_key_id = 'BOA82RVHP6PXW22ZJM61',
            aws_secret_access_key = 'YE9OnzcbgNrQvwHXCww8PZSd4oj5tCrmzil1Kink'
        )

        my_bucket = s3.Bucket('sgg-dev-ai')
        
        my_bucket.download_file(raw_img, "raw_img.jpg")

        fname = 'face'
        n = 0
        fext = '.jpg'
        directory = 'face_images'

        if os.path.exists(directory) == False:
            os.mkdir(directory)

        for face in face_list:
            path = 'face_images/' + fname + str(n) + fext
            my_bucket.download_file(face, path)
            n+=1

        raw_image = Image.open("raw_img.jpg")

        image_list = []

        for filename in os.listdir('face_images'):

            x = Image.open(os.path.join(directory, filename))
            image_list.append(x)

        plt.imshow(raw_image)
        n = len(image_list)
        
        if n != 0:
            if n == 1:
                f, axarr = plt.subplots(1,n)
                for i in range(n):
                    axarr.imshow(image_list[i])
            else:
                f, axarr = plt.subplots(1,n)
                for i in range(n):
                    axarr[i].imshow(image_list[i])

            plt.show()
        else:
            print('No image found!') 

        print('\nwaiting for next Messages...')

    def startserver(self):
        self._channel.basic_consume(
            queue=self.server.queue,
            on_message_callback=rabbitmqServer.callback,
            auto_ack=True)
        self._channel.start_consuming()


if __name__ == "__main__":
    try:
        serverconfigure = RabbitMqServerConfigure(host='localhost',
                                              queue='image')

        server = rabbitmqServer(server=serverconfigure)
        server.startserver()
    except KeyboardInterrupt:
        print("Interrupt")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
