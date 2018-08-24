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
        self.log.info("start dispatch with routing key: {}".format(method.routing_key))
        found = False
        res = json.loads(body)
        do = res['do']

        if 'payload' in res:
            pl = res['payload']

        if do == "insert_mp_doc":
            self.insert_mp_doc(pl)
            found=True

        if do == "insert_auxobj_doc":
            self.insert_auxobj_doc(pl)
            found=True

        if do == "build_mp_db":
            self.build_mp_db(pl['id'])
            found=True
        
        if do == "build_auxobj_db":
            self.build_auxobj_db(pl['id'])
            found=True
        
        if do == "clear_stm":
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
        self.mp_container_db = self.stm['mp_exchange']
        self.mp_container_description_db = self.stm['mp_container_description']
        self.mp_container_definition_db = self.stm['mp_container_definition']
        self.mp_container_element_db = self.stm['mp_container_element']
        self.mp_container_ctrl_db = self.stm['mp_container_ctrl']

        self.stm_mp_db = self.stm['mp']
        self.mp_doc_coll = self.stm_mp_db['mp_doc']
        
        self.stm_auxobj_db = self.stm['auxobj']
        self.auxobj_doc_coll = self.stm_auxobj_db['auxobj_doc']
        
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
            'source':'stm',
            'msg': 'insert_mp_doc_complete',
            'payload':{'id': doc['_id']}
        })
    
    def insert_auxobj_doc(self, doc):
        
        if 'AuxObject' in doc:
            ret = self.auxobj_doc_coll.find({'_id': doc['_id'], '_rev': doc['_rev']})

            if ret.count() == 0:
                res = self.auxobj_doc_coll.insert_one(doc)
                self.log.info("insert with result: {}".format(res))

            if ret.count() == 1:
                self.log.info("doc with same _id and _rev already exists")

            self.ctrl_pub(body_dict={
                'source':'stm',
                'msg': 'insert_auxobj_doc_complete',
                'payload':{'id': doc['_id']}
            })
        else:
            self.log.error("document is not an AuxObject")

    def build_auxobj_db(self, id):
        doc = self.auxobj_doc_coll.find_one({'_id': id})
        doc = doc['AuxObject']

        if 'Default' in doc:
            defaults = doc['default']
        if 'Task' in doc:
            tasks = doc['Task']

        #for ...
        #    self.replace_defaults(task, defaults)             

    def build_mp_db(self, id):
        doc = self.mp_doc_coll.find_one({'_id': id})
        if doc and 'Mp' in doc:
            self.log.info("found document with id: {}, start building collections".format(id))
            mp = doc['Mp']

            if 'Standard' in mp:
                standard = mp['Standard']
            else:
                standard ="none"

            if 'Name' in mp:
                mp_name = mp['Name']
            else:
                mp_name = "none"

            self.write_exchange(id, {"StartTime":{"Type":"start", "Value":self.now()}})

            if 'Exchange' in mp:
                for _, entr in mp['Exchange'].items():
                    self.write_exchange(id, entr)

            for contno, entr in  enumerate(mp['Container']):
                title = entr['Title']
                
                self.mp_container_description_db[id].insert_one({'Description':entr['Description'], 'ContNo':contno, 'Title': title})
                self.mp_container_ctrl_db[id].insert_one({'Ctrl':entr['Ctrl'], 'ContNo':contno, 'Title': title})

                if 'Element' in entr:
                    self.mp_container_element_db[id].insert_one({'Element':entr['Element'], 'ContNo':contno, 'Title': title})
                else:
                    self.mp_container_element_db[id].insert_one({'Element':[], 'ContNo':contno, 'Title': title})

                definition = entr['Definition']
                for serno, _ in enumerate(definition):
                    for parno, _ in enumerate(definition[serno]):

                        t = definition[serno][parno]
                        t['ContNo'] = contno
                        t['SerNo'] = serno
                        t['ParNo'] = parno
                        t['MpName'] = mp_name
                        t['Standard'] = standard

        else:
            m = "can not find document with id: {}".format(id)
            self.log.error(m)
            sys.exit(m)

   

    def write_exchange(self, mpid, doc):
        if isinstance(doc, dict):
            self.mp_container_db[mpid].insert_one(doc)

    def read_exchange(self, id, find_set):
        res = self.mp_container_db[id].find(find_set)
        n = res.count()
        if n == 1:
            print(res[0])
        else:
            print("found nothing")
