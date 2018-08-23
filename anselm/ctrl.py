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
        
        if 'payload' in res:
            pl = res['payload']

        if 'contains' in res:
            contains = res['contains']

        if 'source' in res:
            source = res['source']
            
        if 'msg' in res:
            msg = res['msg']

        if source == "ltm" and contains == "mps":
            self.stm_pub(body_dict={
                'do':"insert_mp_doc",
                'payload':pl
            })
        
        if source == "stm" and msg == "insert_mp_doc_complete":
            self.stm_pub(body_dict={
                'do':"build_mp_db",
                'payload':pl
            })
