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

       
    def get_custobj_ids(self):         
        view_con = self.db_dict.get('view').get('custobj')
        try:
            view = self.db.view(view_con)
            res = [doc.get('id') for doc in view] 
        except Exception as inst:
            self.log.error("cust view does not work: {}".format(inst))
            res = ["dummy cust"]
            self.log.warn("return dummy value")

        return res
    
    def get_cal_ids(self):         
        view_con = self.db_dict.get('view').get('calids')
        year = self.aget('year',0)
        standard = self.aget('standard',0)
        query_key = "{}_{}".format(year, standard)
        
        try:
            view = self.db.view(view_con, key =query_key)
            res = [doc.get('id') for doc in view]
        except Exception as inst:
            self.log.error("doc view does not work: {}".format(inst))
            res = ["dummy doc"]
            self.log.warn("return dummy value")

        return res

    def get_red_doc(self, doc_id):
        doc = self.db[doc_id]
        red_doc = None
        if doc:
            if 'CustomerObject' in doc:
                red_doc = doc.get('CustomerObject')
            
            if 'CalibrationObject' in doc:
                red_doc = doc.get('CalibrationObject')
        else:
            self.log.error("no doc with id {}".format(doc_id))

        if red_doc:   
            return red_doc
        else:
            return None

    def get_tasks(self, doc_id):         
        doc = self.get_red_doc(doc_id)
        if doc and 'Task' in doc:
            return doc.get('Task')
        else:
            return None

    def get_defaults(self, doc_id):         
        doc = self.get_red_doc(doc_id)
        if 'Defaults' in doc:
            defaults = doc.get('Defaults')       
        else:
            defaults = {}

        return defaults

    def get_task(self, doc_id, task_name):         
        doc = self.get_red_doc(doc_id)
        if doc and 'Task' in doc:
            tasks = doc.get('Task')
            for task in tasks:
                if task.get('TaskName') == task_name:
                    break

            return task
        else:
            self.log.error("no doc with id {}".format(doc_id))
            return []

    def get_doc(self, id):
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
    
    def choose_task(self, task_name, line):

        doc_id = self.aget('doc_id', line)
        if doc_id:
            task_db = self.get_task(doc_id, task_name)
            
            # dont get defaults from db
            # they maybe changed for current line

            defaults = self.dget('defaults', line)
        
            if defaults:
                task = self.replace_defaults(task_db, defaults)
                self.log.debug("defaults: {}".format(defaults))
                self.log.debug("task: {}".format(task))

            else:
                self.log.warn("no defaults")

            self.aset('task_name', line, task_name)
            self.aset('task', line, task) 
            self.aset('task_db', line, task_db) 
        else:
            self.log.error("line {} contains no doc_id")

    def save_results(self):
        """
        """
        lines = self.get_lines("cal_id")
        for line in lines:
            cal_id = self.aget("cal_id", line)
            doc = self.get_doc(cal_id)
            doc_path = self.aget("doc_path", line)
            results = self.dget("result", line)
            if doc and doc_path and results:
                for result in results:
                    self.log.debug("""
                                    save components are cal_id {}, 
                                    doc_path_array: {},
                                    result: {}""".format(cal_id, doc_path, result))
                    self.write_result_to_doc(doc, doc_path, result)
                self.store_doc(doc)
                
    
    def write_result_to_doc(self, doc, doc_path, result):
        """Writes result to doc under the given path.
        """
        doc_path_array = doc_path.split(".")
        for key in doc_path_array[:-1]:
            doc = doc.setdefault(key, {})
        if not doc_path_array[-1] in doc:
            doc[doc_path_array[-1]] = []
            doc[doc_path_array[-1]].append(result)
