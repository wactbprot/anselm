import sys
from anselm.system import System
import json

class Ctrl(System):

    def __init__(self):
        super().__init__()

        self.log.info("start long-term memory init function")
        
        self.init_stm_msg_prod()      
        self.init_ltm_msg_prod()      
        self.init_ctrl_msg_prod()
        self.init_ctrl_msg_consume(callback=self.dispatch)

    def dispatch(self, ch, method, props, body):
        res = json.loads(body)
        found = False
        contains = ""
        source = ""
        msg =""

        if 'payload' in res:
            pl = res['payload']

        if 'contains' in res:
            contains = res['contains']
            self.log.info("contains: {}".format(contains))

        if 'source' in res:
            source = res['source']
            self.log.info("source: {}".format(source))
            
            
        if 'msg' in res:
            msg = res['msg']
            self.log.info("msg: {}".format(msg))

        if source == "ltm" and contains == "mpdoc":
            self.stm_pub(body_dict={
                'do':"insert_mp_doc",
                'payload':pl
            })
            found = True
        
        if source == "stm" and msg == "insert_mp_doc_complete":
            self.stm_pub(body_dict={
                'do':"build_mp_db",
                'payload':pl
            })
            found = True

        if found:
            self.log.info("found branch for routing key")
        else:
            self.log.error("no branch found")
