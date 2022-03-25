import pika
from flask import Flask, request, jsonify
from waitress import serve
from PIL import Image
import io

rabbit_host = '172.17.0.2' #use 'localhost' to run locally

app = Flask(__name__)

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