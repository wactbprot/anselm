from anselm.system import System
import couchdb
import json


class LongTermMemory(System):

    def __init__(self):
        super().__init__()
        self.init_log()
        self.init_ltm()

        self.log.info("long-term memory system start consuming")
      
    def init_ltm(self):
        ltm_dict = self.config['couchdb']
        port = ltm_dict['port']
        host = ltm_dict['host']
        url = 'http://{}:{}/'.format(host, port)

        self.ltm_dict = ltm_dict
        self.ltm = couchdb.Server(url)
        self.ltm_db = self.ltm[self.ltm_dict['database']]
        self.log.info("long-term memory system ok")

    def store_doc(self, doc):
        id = doc['_id']
        dbdoc = self.ltm_db[id]
        if dbdoc:
            doc['_rev'] = dbdoc['_rev']
        else:
            doc.pop('_rev', None)

        self.ltm_db.save(doc)

    def get_mps(self):
        view = self.ltm_dict['view']['mpd']
        for mp in self.ltm_db.view(view):
            if mp.id and mp.key == "mpdoc":
                self.ltm_db[mp.id]
               
          
    def get_auxobj(self, id):
        doc = self.ltm_db[id]
        if doc:
            return doc
        else:
            self.log.error("document with id: {} does not exist".format(id))
            return None
        
