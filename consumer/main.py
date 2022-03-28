import io
import pika
import boto3
import psycopg2
import requests
from PIL import Image
import matplotlib.pyplot as plt
import os

from util import Save
from util import Infer

rabbit_host = '172.17.0.2' #use 'localhost' to run locally
db_host = '172.17.0.3' #use 'localhost' to run locally

def callback(ch, m, prop, body):

    image = Image.open(io.BytesIO(body))
    
    fname, image_path = Save.saveImage(image)

    print("Raw image received")

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

    dest = object_folder + "/" + fname
    boto_test_bucket.upload_file(image_path, dest)
    print('Raw image sent to cloud!')

    '''
    database connection
    '''
    connection = psycopg2.connect(
        host=db_host,
        database="mydb",
        user="postgres",
        password="fotoyu"
    )

    '''
    make skema
    '''
    # cur = connection.cursor()

    # tables = (
    #     """
    #     CREATE TABLE users (
    #         id SERIAL PRIMARY KEY
    #     )
    #     """,
    #     """
    #     CREATE TABLE images (
    #         id SERIAL PRIMARY KEY,
    #         user_id INTEGER NOT NULL,
    #         FOREIGN KEY (user_id)
    #             REFERENCES users (id)
    #             ON UPDATE CASCADE ON DELETE CASCADE,
    #         image_link VARCHAR(255) NOT NULL
    #     )
    #     """,
    #     """
    #     CREATE TABLE cropped_images (
    #         id SERIAL PRIMARY KEY,
    #         image_id INTEGER NOT NULL,
    #         FOREIGN KEY (image_id)
    #             REFERENCES images (id)
    #             ON UPDATE CASCADE ON DELETE CASCADE,
    #         cropped_image_link VARCHAR(255) NOT NULL
    #     )
    #     """
    # )

    # for table in tables:
    #     cur.execute(table)

    # cur.close()

    '''
    insert and select in users table
    '''

    cur = connection.cursor()

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
    
    print('Raw image sent to database!')
    results = Infer.get_predict(open(image_path, 'rb'))
    print('Inference success!')

    w, h = image.size
    image_list = []
    name_list = []
    path_list = []

    for box in results['boxes']:
        if int(box[0]) < 0: #left
            box[0] = 0
        if int(box[1]) < 0: #top
            box[1] = 0
        if int(box[2]) > w: #right
            box[2] = w
        if int(box[3]) > h: #bottom
            box[3] = h

        area = (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
        cropped = image.crop(area)
        image_list.append(cropped)

        cropped_fname, cropped_image_path = Save.saveImage(cropped)
        name_list.append(cropped_fname)
        path_list.append(cropped_image_path)

    n = len(image_list)
    if n != 0:

        con = psycopg2.connect(
            host=db_host,
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

        a = 0

        for i in range(n):
            image_path = path_list[i]
            image_name = 'face_images/' + name_list[i]
            destination = object_folder + '/' + image_name

            boto_test_bucket.upload_file(image_path, destination)

            cur.execute("insert into cropped_images (image_id, cropped_image_link) values (%s, %s)",
                        (raw_image_id, destination))

            con.commit()
            a+=1
        con.close()

        if n == 1:
            f, axarr = plt.subplots(1,a)
            for i in range(n):
                axarr.imshow(image_list[i])
        else:
            f, axarr = plt.subplots(1,a)
            for i in range(n):
                axarr[i].imshow(image_list[i])
            
        plt.show()

    print(f'Detection complete! Total face found: {a}')

def main():
    host = rabbit_host
    exchange = 'exchange_img'
    queue = 'Q_image'

    conn = pika.BlockingConnection(pika.ConnectionParameters(host))
    chan = conn.channel()

    chan.exchange_declare(exchange, exchange_type='fanout')
    chan.queue_declare(queue, durable=True)

    chan.queue_bind(queue, exchange)

    chan.basic_consume(queue, callback, auto_ack=True)

    print('Waiting for messages... CTRL+C to exit')
    chan.start_consuming()

if __name__ == '__main__':   
    try:
        main()
    except KeyboardInterrupt:
        print('Exit...')
        exit()