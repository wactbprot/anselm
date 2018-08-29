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
   
     
    def get_task(self, id, taskname):
        task = self.stm[id]['tasks'].find({"TaskName": taskname})
        n = task.count()
        if n > 0:
            return task[n-1]
    
    def get_tasknames(self, id):
        tasks = self.stm[id]['tasks'].find()
        for task in tasks:
            print(task['TaskName'])    
        
        
        
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
