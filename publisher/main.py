import pika
from flask import Flask, request, jsonify
from waitress import serve
from PIL import Image
import io
import psycopg2
import boto3
import os
import matplotlib.pyplot as plt
import json

rabbit_host = '172.17.0.2' #use 'localhost' to run locally
db_host = '172.17.0.3'

app = Flask(__name__)

@app.route("/image/<string:id>", methods=["GET"])
def get_result(id):

    user_id = id

    connection = psycopg2.connect(
        host=db_host,
        database="mydb",
        user="postgres",
        password="fotoyu"
    )

    cur = connection.cursor()

    cur.execute("select id from users order by id DESC")

    rows = cur.fetchall()

    newest_id = None
    for r in rows:
        test = r[0]
        if int(test) == int(user_id):
            newest_id = int(test)
            break
    
    if newest_id is None:
        return f'invalid user id {user_id}', 400

    cur.execute("SELECT i.image_link, c.cropped_image_link FROM users u JOIN images i on i.user_id = u.id JOIN cropped_images c on c.image_id = i.id WHERE u.id = %s", (newest_id, ))

    res = cur.fetchall()

    face_list = []
    for r1 in res:
        raw_img = r1[0]
        face_list.append(r1[1])

    connection.close()

    if newest_id is None:
        return f'invalid user id {raw_img} {face_list}', 400

    output = dict()
    output['raw_image_url'] = f'https://s3.wasabisys.com/sgg-dev-ai/{raw_img}'
    output['faces'] = {'face_image_url': []}

    for face in face_list:
        face_path = f'https://s3.wasabisys.com/sgg-dev-ai/{face}'
        output['faces']['face_image_url'].append(face_path)
    
    return output

@app.route("/image", methods=["POST"])
def process_image():

    file = request.files['image']
    # Read the image via file.stream
    img = Image.open(file.stream)

    b = io.BytesIO()
    img.save(b, 'jpeg')
    im_bytes = b.getvalue()

    channel.basic_publish(exchange, '', im_bytes, properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE))

    print('image succesfully sent!')
    return jsonify({'msg': 'success', 'size': [img.width, img.height]})

if __name__ == '__main__':
    try:

        host = rabbit_host
        exchange = 'exchange_img'
        queue = 'Q_image'
            
        connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        channel = connection.channel()

        channel.exchange_declare(exchange, exchange_type='fanout')
        channel.queue_declare(queue, durable=True)

        channel.queue_bind(queue, exchange)

    except KeyboardInterrupt:
        print('Exit...')
        exit()

    port = 3000
    
    print('waiting for inputs..')
    serve(app, host='0.0.0.0', port=port)