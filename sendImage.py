import pika
import os
import sys
import json
import tkinter as tk
from tkinter import filedialog

class MetaClass(type):

    _instance = {}

    def __call__(cls, *args, **kwargs):
        """ Singelton Design Pattern  """

        if cls not in cls._instance:
            cls._instance[cls] = super(
                MetaClass, cls).__call__(*args, **kwargs)
            return cls._instance[cls]


class RabbitmqConfigure(metaclass=MetaClass):

    def __init__(self, queue='image', host='localhost', routingKey='image', exchange=''):
        """ Configure Rabbit Mq Server  """
        self.queue = queue
        self.host = host
        self.routingKey = routingKey
        self.exchange = exchange


class RabbitMq():

    __slots__ = ["server", "_channel", "_connection"]

    def __init__(self, server):
        """
        :param server: Object of class RabbitmqConfigure
        """

        self.server = server
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.server.host))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue=self.server.queue)

    def __enter__(self):
        print("__enter__")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("__exit__")
        self._connection.close()

    def publish(self, payload={}):
        """
        :param payload: JSON payload
        :return: None
        """

        self._channel.basic_publish(exchange=self.server.exchange,
                                    routing_key=self.server.routingKey,
                                    body=str(payload))

        print("Image sent succesfully!")


class Image(object):

    __slots__ = ["filename"]

    def __init__(self, filename):
        self.filename = filename

    @property
    def get(self):
        with open(self.filename, "rb") as f:
            data = f.read()
        return data


if __name__ == "__main__":

    server = RabbitmqConfigure(queue='image',
                               host='localhost',
                               routingKey='image',
                               exchange='')

    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()

    image = Image(filename=file_path)
    data = image.get

    with RabbitMq(server) as rabbitmq:
        rabbitmq.publish(payload=data)
