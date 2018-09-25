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

       
    def get_device_ids(self):         
        view_con = self.db_dict.get('view').get('devices')
        try:
            view = self.db.view(view_con)
            res = [doc.get('id') for doc in view] 
        except Exception as inst:
            self.log.error("device view does not work: {}".format(inst))
            res = ["dummy device"]
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
            
            if 'DeviceClass' in doc:
                red_doc = doc.get('DeviceClass')
            
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

    def set_doc(self, doc):
        self.log.info("try to save document")
        res = self.db.save(doc)
        self.log.info(res)
        
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
        lines = self.get_lines('cal_id')
        for line in lines:
            doc_path = self.aget("doc_path", line)
            results = self.dget("result", line)
            cal_id = self.aget("cal_id", line)
            if cal_id and doc_path and results:
                doc = self.get_doc(cal_id)
                self.log.debug("try to save results: {}".format(results))
                for result in results:
                    self.log.debug("components are cal_id {}, doc_path_array: {}, result: {} saved".format(cal_id, doc_path, result))
                    self.doc_write_result(doc, doc_path, result)
                    self.adelete("result", line)
                    self.log.debug("deleted result of line {} from mem".format(line))
                self.set_doc(doc)
    
    def doc_write_result(self, doc, doc_path, result):
        #
        # last entry is something like Pressure (Type, Value and Unit) 
        # or (!) OperationKind 
        #
        doc_path_array = doc_path.split(".")
        last_entr = doc_path_array[-1]  

        for key in doc_path_array[:-1]:
            doc = doc.setdefault(key, {})

        if isinstance(result, dict):
            if 'Type' in result and 'Value' in result:
                if last_entr not in doc:
                    result = self.ensure_result_struct(result)
                    doc[last_entr] = []
                    doc[last_entr].append(result)
                else:
                    found = False
                    for entr in doc[last_entr]:
                        if entr.get('Type') == result.get('Type'):
                            found = True
                            if isinstance(result.get('Value'), list) and len(result.get('Value')) > 1: 
                                self.log.debug("value is list an length > 1, overwrite")
                                entr['Value'] = result.get('Value') # override
                                entr['Unit'] = result.get('Unit')
                                if result.get('SdValue'):
                                    if entr.get('SdValue'):
                                        entr['SdValue'] = result['SdValue'] 
                                if result.get('N'):
                                    if entr.get('N'):
                                        entr['N'] = result['N'] 
                            else:
                                entr['Value'].append( result['Value'] )
                                entr['Unit'] = result['Unit']
                                if result.get('SdValue'):
                                    if entr.get('SdValue'):
                                        entr['SdValue'].append( result['SdValue'] )
                                if result.get('N'):
                                    if entr.get('N'):
                                        entr['N'].append( result['N'] )
                    if not found:
                        result = self.ensure_result_struct(result)
                        doc[last_entr].append(result)
            else:
                result = self.ensure_result_struct(result)
                doc[last_entr] = result   
        else:
            doc[last_entr] = result       

    def ensure_result_struct(self, result):

        if not isinstance(result['Value'], list):
            result['Value'] = [result['Value']] 
        if result.get('SdValue') and not isinstance(result['SdValue'], list):
            result['SdValue'] = [result['SdValue']]
        if result.get('N') and not isinstance(result['N'], list):
            result['N'] = [result['N']]

        return result