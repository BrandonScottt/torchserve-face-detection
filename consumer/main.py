import io
import pika
import boto3
import psycopg2
import requests
from PIL import Image

from util import Save

rabbit_host = 'localhost'
db_host = 'localhost'

def callback(ch, m, prop, body):

    image = Image.open(io.BytesIO(body))
    
    fname, image_path = Save.saveImage(image)

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
        host=db_host,
        database="mydb",
        user="postgres",
        password="fotoyu"
    )

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
    
    print('Image sent to database!')
    res = requests.post("http://localhost:8080/predictions/mymodel" , files={'data': open(image_path, 'rb')})

    print('Detection complete!')

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