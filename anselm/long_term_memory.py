from anselm.system import System
import couchdb
import json


class LongTermMemory(System):

    def __init__(self):
        super().__init__()
        self.init_log()
        self.init_ltm()

        self.log.info("long-term memory system start consuming")
        self.init_stm_msg_prod()
        self.init_ltm_msg_prod()
        self.init_ltm_msg_consume()

    def dispatch(self, ch, method, props, body):
        res = json.loads(body)
        do = res['do']
        if 'payload' in res:
            pl = res['payload']

        if do == "start":
            self.get_mp_defs()

        if do == "store_doc":
            self.store_doc(pl)

        self.log.info("dispatch to do: {}".format(do))


    def init_ltm(self):
        ltm_dict = self.config['couchdb']
        port = ltm_dict['port']
        host = ltm_dict['host']
        url = 'http://{}:{}/'.format(host, port)

        self.ltm_dict = ltm_dict
        self.ltm = couchdb.Server(url)
        self.ltm_db = self.ltm[self.ltm_dict['database']]
        self.ltm_db_sav = self.ltm["{}_sav".format(self.ltm_dict['database'])]
        self.log.info("long-term memory system ok")

    def store_doc(self, doc):
        id = doc['_id']
        dbdoc = self.ltm_db_sav[id]
        if dbdoc:
            doc['_rev'] = dbdoc['_rev']
        else:
            doc.pop('_rev', None)

        self.ltm_db_sav.save(doc)

    def get_mp_defs(self):
        view = self.ltm_dict['view']['mpd']
        for mp in self.ltm_db.view(view):
            if mp.id and mp.key == "mpdoc":
                doc = self.ltm_db[mp.id]
                self.stm_pub(body_dict={
                            'do':'insert_document',
                            'payload':doc}
                            )
            else:
                self.log.info(
                    "document with id: {} will not be published".format(mp.id))
