from anselm.system import System
from pymongo import MongoClient
import json
import pika
import coloredlogs
import logging


class ShortTermMemory(System):

    def __init__(self):
        super().__init__()

        self.log.info("start long-term memory init function")

        stm_dict = self.config['mongodb']

        self.stm_dict = stm_dict

        port = stm_dict['port']
        host = stm_dict['host']

        self.stm = MongoClient(host, port)

        msg_dict = self.config['rabbitmq']
        host = msg_dict['host']
        param = pika.ConnectionParameters(host=host)

        conn = pika.BlockingConnection(param)

        chan = conn.channel()
        chan.exchange_declare(exchange='stm',
                              exchange_type='topic')

        result = chan.queue_declare(exclusive=True)
        queue_name = result.method.queue

        chan.queue_bind(exchange='stm',
                        routing_key='stm.*.*',
                        queue=queue_name)

        chan.basic_consume(self.dispatch,
                           queue=queue_name,
                           no_ack=True)
        self.init_stm()

        self.log.info("short-term memory system start consuming")
        chan.start_consuming()

    def dispatch(self, ch, method, props, body):
        self.log.info("start dispatch with routing key: {}".format(method.routing_key))

        if method.routing_key == "stm.insert.document":
            self.log.info("found case fore routing key"
            doc = json.loads(body)
            self.insert_doc(doc)

    def init_stm(self):
        self.stm_db = self.stm['mp_def']
        self.exchange_db = self.stm['exchange']

        self.log.info("generate database")
        self.doc_coll = self.stm_db['doc']
        self.log.info("generate doc collection")
        self.log.info("short-term memory system ok")

    def insert_doc(self, doc):
        ret = self.doc_coll.find({'_id': doc['_id'], '_rev': doc['_rev']})

        if ret.count() == 0:
            res = self.doc_coll.insert_one(doc)
            self.log.info("insert with result: {}".format(res))

        if ret.count() == 1:
            self.log.info("doc with same _id and _rev already exists")

    def build_api(self, id):
        doc = self.doc_coll.find({'_id': id})
        if doc.count() == 1:
            self.log.info("found document, start building collections")
            # collection with id to exchange database
            self.exchange_db[id].insert_one({Time:{Type:"start", Value:10}})
