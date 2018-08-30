from anselm.system import System
import couchdb
import json


class DB(System):

    def __init__(self):
        super().__init__()
        self.init_db()

        self.log.info("database ")
      
    def init_db(self):
        db_dict = self.config['couchdb']
        port = db_dict['port']
        host = db_dict['host']
        url = 'http://{}:{}/'.format(host, port)

        self.db_dict = db_dict
        self.db = couchdb.Server(url)
        self.db_db = self.db[self.db_dict['database']]
        self.log.info("long-term memory system ok")

    def store_doc(self, doc):
        id = doc['_id']
        dbdoc = self.db_db[id]
        if dbdoc:
            doc['_rev'] = dbdoc['_rev']
        else:
            doc.pop('_rev', None)

        self.db_db.save(doc)

    def get_mps(self):
        view = self.db_dict['view']['mpd']
        for mp in self.db_db.view(view):
            if mp.id and mp.key == "mpdoc":
                self.db_db[mp.id]
    
    def get_auxobj_ids(self):         
        view = self.db_dict['view']['auxobj']
        
        return [doc['id'] for doc in self.db_db.view(view)]
            

    def get_auxobj(self, id):
        doc = self.db_db[id]
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
