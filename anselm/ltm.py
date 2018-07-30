from anselm.system import System

import json
import couchdb
import pika
import coloredlogs
import logging


class LongTermMemory(System):

    def __init__(self):
        super().__init__()
        self.log.info("start long-term memory init function")
        msg_dict = self.config['rabbitmq']
        host = msg_dict['host']
        self.msg_param = pika.ConnectionParameters(host=host)

        self.init_log()
        self.init_ltm()

        self.log.info("long-term memory system start consuming")
        self.init_stm_msg_prod()
        self.init_msg_consume()

    def dispatch(self, ch, method, props, body):
        self.log.info(
            "here comes dispatch with routing key: {}".format(method.routing_key))
        if method.routing_key == "ltm.all":
            self.get_mpd()

    def init_stm_msg_prod(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.exchange_declare(exchange='stm',
                              exchange_type='topic')
        self.stm_conn = conn
        self.stm_chan = chan

    def init_msg_consume(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.exchange_declare(exchange='ltm',
                              exchange_type='topic')

        result = chan.queue_declare(exclusive=True)
        queue_name = result.method.queue
        chan.queue_bind(exchange='ltm',
                        routing_key='ltm.#',
                        queue=queue_name)

        chan.basic_consume(self.dispatch,
                           queue=queue_name,
                           no_ack=True)

        chan.start_consuming()

    def init_ltm(self):
        ltm_dict = self.config['couchdb']
        port = ltm_dict['port']
        host = ltm_dict['host']
        url = 'http://{}:{}/'.format(host, port)

        self.ltm_dict = ltm_dict
        self.ltm = couchdb.Server(url)
        self.ltm_db = self.ltm[self.ltm_dict['database']]
        self.log.info("long-term memory system ok")

    def get_mpd(self):
        view = self.ltm_dict['view']['mpd']
        for mp in self.ltm_db.view(view):
            if mp.id and mp.key == "mpdoc":
                doc = self.ltm_db[mp.id]
                self.stm_chan.basic_publish(exchange='stm',
                                            routing_key='stm.build.database',
                                            body=json.dumps(doc))
            else:
                self.log.info(
                    "document with id: {} will not be published".format(mp.id))
