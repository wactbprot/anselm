import sys
from anselm.system import System
from pymongo import MongoClient
import json

class ShortTermMemory(System):

    def __init__(self):
        super().__init__()

        self.log.info("start long-term memory init function")

        stm_dict = self.config['mongodb']
        self.stm_dict = stm_dict
        self.stm = MongoClient(stm_dict['host'], stm_dict['port'])
        self.init_stm()

        self.init_ctrl_msg_prod()
        self.init_stm_msg_consume(callback=self.dispatch)

    def dispatch(self, ch, method, props, body):
        found = False
        do, pl = self.parse_body(body)

        if do == "insert_mp_doc":
            self.insert_mp_doc(pl)
            found=True

        if do == "build_mp_db":
            self.build_mp_db(pl['id'])
            found=True

        if do == "clear_all":
            self.clear_stm()
            found=True

        if do == "read_exchange":
            self.read_exchange(pl['id'], pl['find_set'])
            found=True

        if do == "mp_to_ltm":
            self.mp_to_ltm(pl['id'])
            found=True

        if found:
            self.log.info("found branch for routing key")
        else:
            self.log.error("no branch found for routing key: {}".format(do))

    def init_stm(self):
        """Generates the api databases and the source doc collection.
        """
        self.exchange_db = self.stm['mp_exchange']
        self.container_description_db = self.stm['mp_container_description']
        self.container_definition_db = self.stm['mp_container_definition']
        self.container_element_db = self.stm['mp_container_element']
        self.container_ctrl_db = self.stm['mp_container_ctrl']

        self.stm_mp_db = self.stm['mp_def']
        self.mp_doc_coll = self.stm_mp_db['mp_doc']

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

    def mp_to_ltm(self, id):
        doc = self.mp_doc_coll.find({'_id': id})
        n = doc.count()
        self.ltm_pub(body_dict={
                        'do':'store_doc',
                        'payload': doc[n-1]
                        })

    def insert_mp_doc(self, doc):
        ret = self.mp_doc_coll.find({'_id': doc['_id'], '_rev': doc['_rev']})

        if ret.count() == 0:
            res = self.mp_doc_coll.insert_one(doc)
            self.log.info("insert with result: {}".format(res))

        if ret.count() == 1:
            self.log.info("doc with same _id and _rev already exists")

        self.ctrl_pub(body_dict={
            'source':'ltm'
            'msg': 'insert_mp_doc_comlete',
            'payload':doc['_id']
        })

    def build_mp_db(self, id):
        doc = self.mp_doc_coll.find_one({'_id': id})
        if doc and 'Mp' in doc:
            mp = doc['Mp']
            self.log.info("found document, start building collections")
            standard = mp['Standard']
            mp_name = mp['Name']
            # start with filling up exchange
            self.write_exchange(id, {"StartTime":{"Type":"start", "Value":self.now()}})

            if 'Exchange' in mp:
                for _, entr in mp['Exchange'].items():
                    self.write_exchange(id, entr)

            for contno, entr in  enumerate(mp['Container']):
                title = entr['Title']
                self.container_description_db[id].insert_one({'Description':entr['Description'], 'ContNo':contno, 'Title': title})
                self.container_element_db[id].insert_one({'Element':entr['Element'], 'ContNo':contno, 'Title': title})
                self.container_ctrl_db[id].insert_one({'Ctrl':entr['Ctrl'], 'ContNo':contno, 'Title': title})

                definition = entr['Definition']
                for serno, _ in enumerate(definition):
                    for parno, _ in enumerate(definition[serno]):

                        t = definition[serno][parno]
                        t['ContNo'] = contno
                        t['SerNo'] = serno
                        t['ParNo'] = parno
                        t['MpName'] = mp_name
                        t['Standard'] = standard

                        self.ltm_pub(body_dict={'do':'provide_task', 'payload':t})
        else:

            m = "can not find document with id: {}".format(id)
            self.log.error(m)
            sys.exit(m)



    def write_exchange(self, mpid, doc):
        if isinstance(doc, dict):
            self.exchange_db[mpid].insert_one(doc)

    def read_exchange(self, id, find_set):
        res = self.exchange_db[id].find(find_set)
        n = res.count()
        if n == 1:
            print(res[0])
        else:
            print("found nothing")
