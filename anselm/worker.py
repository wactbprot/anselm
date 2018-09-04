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
        

    def run(self, task, line):
        acc = task['Action']

        if acc == "TCP":
            self.relay_worker(task, line)
        if acc == "VXI11":
            self.relay_worker(task, line)
    
    def relay_worker(self, task, line):
        req = requests.post(self.relay_url, data=json.dumps(task), headers = self.headers)
        res = req.json()
        if 'Result' in res:
            self.aset('result', line,  res['Result'])
            print(res['Result'])
          

        if 'ToExchange' in res:
            self.aset('exchange', line, res['ToExchange'])
            print(res['ToExchange'])
        