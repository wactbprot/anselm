from anselm.system import System
from pymongo import MongoClient
import json
import pika
import coloredlogs, logging


class ShortTermMemory(System):

    def __init__(self):
        super().__init__()

        self.log.info("start long-term memory init function")

        msg_dict = self.config['rabbitmq']
        host = msg_dict['host']
        param = pika.ConnectionParameters(host=host)

        conn = pika.BlockingConnection(param)

        channel = conn.channel()
        channel.exchange_declare(exchange='stm',
                                 exchange_type='topic')

        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange='stm',
                            routing_key='stm.#',
                            queue=queue_name)

        channel.basic_consume(self.dispatch,
                              queue=queue_name,
                              no_ack=True)

        self.init_stm()

        self.log.info("short-term memory system start consuming")
        channel.start_consuming()

    def dispatch(self, ch, method, props, body):
        self.log.info("here comes dispatch with routing key: {}".format(method.routing_key))
        if method.routing_key == "stm.push_mp":
            self.log.info("received")
    def init_stm(self):
        mongodb_dict = self.config['mongodb']
        port = mongodb_dict['port']
        host = mongodb_dict['host']
        self.stm = MongoClient(host, port)
        self.log.info("short-term memory system ok")
