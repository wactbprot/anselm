from anselm.system import System
import couchdb
import json


class LongTermMemory(System):

    def __init__(self):
        super().__init__()
        self.init_log()
        self.init_ltm()

        self.log.info("long-term memory system start consuming")
        self.init_ctrl_msg_prod()
        self.init_ltm_msg_consume(callback=self.dispatch)

    def dispatch(self, ch, method, props, body):
        res = json.loads(body)
        do = res['do']
        found = False

        if 'payload' in res:
            pl = res['payload']
            found = True

        if do == "get_mps":
            self.get_mps()
            found = True

        if do == "store_doc":
            self.store_doc(pl)
            found = True

        if found:
            self.log.info("dispatch to do: {}".format(do))
        else:
            self.log.error("found no dispatch case for {}".format(do))

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
                doc = self.ltm_db[mp.id]
                self.ctrl_pub(body_dict={
                            'contains':'mpdoc',
                            'source':'ltm',
                            'payload': doc}
                            )
            else:
                self.log.info(
                    "document with id: {} will not be published".format(mp.id))
