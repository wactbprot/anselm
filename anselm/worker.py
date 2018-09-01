import requests
import json
from anselm.system import System


class Worker(System):


    def __init__(self):
        super().__init__()
        relay_dict = self.config['relay']
        self.relay_dict = relay_dict
        self.relay_url = "http://{}:{}".format(relay_dict['host'], relay_dict['port'])
        self.headers = {'content-type': 'application/json'}
        

    def run(self, task):
        acc = task['Action']

        if acc == "TCP":
            self.relay_worker(task)
    
    def relay_worker(self, task):
        req = requests.post(self.relay_url, data=json.dumps(task), headers = self.headers)
        res = req.json()
        
        if 'Result' in res:
            print(res['Result'])
            print(self.state)
            print("dddddddddddddddddd")

        if 'ToExchange' in res:
            print(res['ToExchange'])
        