import sys
from anselm.system import System
from pymongo import MongoClient
import json
import pika
import coloredlogs
import logging
import datetime


class ShortTermMemory(System):

    def __init__(self):
        super().__init__()

        self.log.info("start long-term memory init function")

        stm_dict = self.config['mongodb']
        self.stm_dict = stm_dict
        self.stm = MongoClient(stm_dict['host'], stm_dict['port'])
        self.init_stm()

        msg_dict = self.config['rabbitmq']
        self.msg_param = pika.ConnectionParameters(host=msg_dict['host'])
        self.init_msg_consume()


    def init_msg_consume(self):
        conn = pika.BlockingConnection(self.msg_param)
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
                           no_ack=False)

        self.log.info("short-term memory system start consuming")
        chan.start_consuming()

    def dispatch(self, ch, method, props, body):
        self.log.info("start dispatch with routing key: {}".format(method.routing_key))
        found = False
        if method.routing_key == "stm.insert.document":
            o = json.loads(body)
            self.insert_source_doc(o)
            found=True

        if method.routing_key == "stm.build.api":
            o = json.loads(body)
            self.build_api(o['id'])
            found=True

        if method.routing_key == "stm.clear.all":
            self.clear_stm()
            found=True

        if method.routing_key == "stm.read.exchange":
            o = json.loads(body)
            self.read_exchange(o['id'], o['find_set'])
            found=True

        if found:
            self.log.info("found branch for routing key")
        else:
            self.log.error("no branch found for routing key: {}".format(method.routing_key))

    def init_stm(self):
        """Generates the api databases and the source doc collection.
        """
        self.exchange_db = self.stm['mp_exchange']
        self.container_description_db = self.stm['mp_container_description']
        self.container_definition_db = self.stm['mp_container_definition']
        self.container_element_db = self.stm['mp_container_element']
        self.container_ctrl_db = self.stm['mp_container_ctrl']

        self.stm_source_db = self.stm['mp_def']
        self.source_doc_coll = self.stm_source_db['source_doc']

        self.log.info("short-term memory system ok")

    def clear_stm(self):
        """
        Clears the stm by droping all databasese starting with ``mp_``.
        """
        n=0
        for database in self.stm.database_names():
            if database.startswith("mp_"):
                n=n+1
                self.stm.drop_database(database)
                self.log.info("drop databes {}".format(database))

        self.log.info("amount of droped databases: {}".format(n))
        
    def insert_source_doc(self, doc):
        ret = self.source_doc_coll.find({'_id': doc['_id'], '_rev': doc['_rev']})

        if ret.count() == 0:
            res = self.source_doc_coll.insert_one(doc)
            self.log.info("insert with result: {}".format(res))

        if ret.count() == 1:
            self.log.info("doc with same _id and _rev already exists")

    def build_api(self, id):
        doc = self.source_doc_coll.find_one({'_id': id})
        if doc:
            self.log.info("found document, start building collections")
            d = datetime.datetime.now().isoformat().replace('T', ' ')
            self.write_exchange(id, {"StartTime":{"Type":"start", "Value":d}})

            for i, entr in  enumerate(doc['Mp']['Container']):
                title = entr['Title']
                self.container_description_db[id].insert_one({'Description':entr['Description'], 'No':i, 'Title': title})
                self.container_definition_db[id].insert_one({'Definition':entr['Definition'], 'No':i, 'Title': title})
                self.container_element_db[id].insert_one({'Element':entr['Element'], 'No':i, 'Title': title})
                self.container_ctrl_db[id].insert_one({'Ctrl':entr['Ctrl'], 'No':i, 'Title': title})

        else:
            m = "can not find document with id: {}".format(id)
            self.log.error(m)
            sys.exit(m)

    def write_exchange(self, id, doc):
        self.exchange_db[id].insert_one(doc)

    def read_exchange(self, id, find_set):
        res = self.exchange_db[id].find(find_set)
        n = res.count()
        if n > 0:
            print(res[n-1])
        else:
            print("found nothing")
