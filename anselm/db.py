from anselm.system import System
import couchdb
import json

class DB(System):

    def __init__(self):
        super().__init__()
        self.init_db()

        self.log.info("database ")
      
    def init_db(self):
        db_dict = self.config.get('couchdb')
        port = db_dict.get('port')
        host = db_dict.get('host')
        url = 'http://{}:{}/'.format(host, port)

        self.db_dict = db_dict
        self.db_srv = couchdb.Server(url)
        self.db = self.db_srv[self.db_dict['database']]
        self.log.info("database  ok")

    def store_doc(self, doc):
        id = doc.get('_id')
        dbdoc = self.db[id]
        if dbdoc:
            doc['_rev'] = dbdoc.get('_rev')
        else:
            doc.pop('_rev', None)

        self.db.save(doc)

       
    def get_auxobj_ids(self):         
        view = self.db_dict.get('view').get('auxobj')
        
        return [doc.get('id') for doc in self.db.view(view)]
    
    def get_red_doc(self, doc_id):
        doc = self.db[doc_id]
        red_doc = None
        if doc:
            if 'AuxObject' in doc:
                red_doc = doc.get('AuxObject')
            
            if 'CalibrationObject' in doc:
                red_doc = doc.get('CalibrationObject')
        else:
            self.log.error("no doc with id {}".format(doc_id))

        if red_doc:   
            return red_doc
        else:
            return None

    def get_task_names(self, doc_id):         
        doc = self.get_red_doc(doc_id)
        if doc and 'Task' in doc:
            return [task.get('TaskName') for task in doc.get('Task')]
        else:
            return []
        
    def get_task(self, doc_id, task_name):         
        doc = self.get_red_doc(doc_id)
        if doc and 'Task' in doc:
            tasks = doc.get('Task')
            for task in tasks:
                if task.get('TaskName') == task_name:
                    break

            if 'Defaults' in doc:
                defaults = doc.get('Defaults')       
                task = self.replace_defaults(task=task, defaults=defaults)

            return task
        else:
            self.log.error("no doc with id {}".format(doc_id))
            return []

    def get_auxobj(self, id):
        doc = self.db[id]
        if doc:
            return doc
        else:
            self.log.error("document with id: {} does not exist".format(id))
            return None
        
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
