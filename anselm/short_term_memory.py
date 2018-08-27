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

        self.init_ctrl_msg_prod()
        self.init_msg_consume(queue_name='stm', callback=self.dispatch)

    def dispatch(self, ch, method, props, body):
        self.log.info("start dispatch with routing key: {}".format(method.routing_key))
        found = False
        res = json.loads(body)
        do = res['do']

        if 'payload' in res:
            pl = res['payload']

        if do == "build_mp_db":
            self.build_mp_db(pl)
            found=True

        if do == "build_auxobj_db":
            self.build_auxobj_db(pl)
            found=True

        if do == "clear_stm":
            self.clear_stm()
            found=True

        if do == "mp_to_ltm":
            self.mp_to_ltm(pl['id'])
            found=True
        
        if do == "trigger_run_task":
            self.trigger_run_task(pl['id'], pl['task'])
            found=True

        if found:
            self.log.info("found branch for routing key")
        else:
            self.log.error("no branch found for routing key: {}".format(do))

    def trigger_run_task(self, id, taskname, cdid=False):
        task = self.stm[id]['tasks'].find({"TaskName": taskname})
        n = task.count()

        print(task[n-1])
        self.ctrl_pub(body_dict={
                        'source':'stm',
                        'contains': 'task',
                        'payload': {'id': id, 'task': task[n-1]}
                        })

    def clear_stm(self):
        """
        Clears the stm by droping all databasese.
        """
        n=0
        for database in self.stm.database_names():          
            n=n+1
            self.stm.drop_database(database)
            self.log.info("drop databes {}".format(database))

        self.log.info("amount of droped databases: {}".format(n))

    def mp_to_ltm(self, id):
        doc = self.stm[id]['org'].find({'_id': id})
        n = doc.count()
        self.ltm_pub(body_dict={
                        'do':'store_doc',
                        'payload': doc[n-1]
                        })

    def build_auxobj_db(self, doc):

        if '_id' in doc:
            id = doc['_id']

        db = self.stm[id]
        db_coll_org = db['org']
        db_coll_org = doc

        db_coll_task = db['tasks']

        if 'AuxObject' in doc:
            doc = doc['AuxObject']

            
        if 'Defaults' in doc:
            defaults = doc['Defaults']
        else:
            self.log.warning("no defaults in AuxObject with id: {}".format(id))

        if 'Task' in doc:
            tasks = doc['Task']
        else:
            self.log.error("no task in AuxObject with id: {}".format(id))

        if 'tasks' in locals() and 'defaults' in locals():
            for _, task in  enumerate(tasks):
                task = self.replace_defaults(task, defaults) 
                task['_id'] = "{}@{}".format(task['TaskName'], id)

                db_coll_task.insert_one(task)
        
        self.ctrl_pub(body_dict={
                'source':'stm',
                'msg': 'build_auxobj_db_complete',
                'payload':{'id': id}
            })
   
    def replace_defaults(self, task, defaults):
        strtask = json.dumps(task)
        if isinstance(defaults, dict):
            for key, val in defaults.items():
                if isinstance(val, int) or isinstance(val, float):
                    val = '{}'.format(val)
                val = val.replace('\n', '\\n')
                val = val.replace('\r', '\\r')
                
                strtask = strtask.replace(key, val)
        else:
            self.log.error("defaults is not a dict")

        try:
            task = json.loads(strtask)
        except:
            self.log.error("replacing defaults fails for")

        return task
    
    def build_mp_db(self, id):
        pass
#        doc = self.{'_id': id})
#        if doc and 'Mp' in doc:
#            self.log.info("found document with id: {}, start building collections".format(id))
#            mp = doc['Mp']
#
#            if 'Standard' in mp:
#                standard = mp['Standard']
#            else:
#                standard ="none"
#
#            if 'Name' in mp:
#                mp_name = mp['Name']
#            else:
#                mp_name = "none"
#
#            self.write_exchange(id, {"StartTime":{"Type":"start", "Value":self.now()}})
#
#            if 'Exchange' in mp:
#                for _, entr in mp['Exchange'].items():
#                    self.write_exchange(id, entr)
#
#            for contno, entr in  enumerate(mp['Container']):
#                title = entr['Title']
#
#                self.mp_container_description_db[id].insert_one({'Description':entr['Description'], 'ContNo':contno, 'Title': title})
#                self.mp_container_ctrl_db[id].insert_one({'Ctrl':entr['Ctrl'], 'ContNo':contno, 'Title': title})
#
#                if 'Element' in entr:
#                    self.mp_container_element_db[id].insert_one({'Element':entr['Element'], 'ContNo':contno, 'Title': title})
#                else:
#                    self.mp_container_element_db[id].insert_one({'Element':[], 'ContNo':contno, 'Title': title})
#
#                definition = entr['Definition']
#                for serno, _ in enumerate(definition):
#                    for parno, _ in enumerate(definition[serno]):
#
#                        t = definition[serno][parno]
#                        t['ContNo'] = contno
#                        t['SerNo'] = serno
#                        t['ParNo'] = parno
#                        t['MpName'] = mp_name
#                        t['Standard'] = standard
#
#        else:
#            m = "can not find document with id: {}".format(id)
#            self.log.error(m)
#            sys.exit(m)
#


#    def write_exchange(self, mpid, doc):
#        if isinstance(doc, dict):
#            self.mp_container_db[mpid].insert_one(doc)

#    def read_exchange(self, id, find_set):
#        res = self.mp_container_db[id].find(find_set)
#        n = res.count()
#        if n == 1:
#            print(res[0])
#        else:
#            print("found nothing")
