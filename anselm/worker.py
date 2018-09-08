import requests
import json
from anselm.system import System


class Worker(System):


    def __init__(self):
        super().__init__()
        relay_dict = self.config.get('relay')
        self.relay_dict = relay_dict
        self.relay_url = "http://{}:{}".format(relay_dict.get('host'), relay_dict.get('port')
        self.headers = {'content-type': 'application/json'}
        

    def run(self, task, line, callback=None):
        acc = task['Action']

        if acc == "TCP":
            self.relay_worker(task, line, callback)
        if acc == "VXI11":
            self.relay_worker(task, line, callback)
    
    def relay_worker(self, task, line, callback):
        req = requests.post(self.relay_url, data=json.dumps(task), headers = self.headers)
        res = req.json()
        if 'Result' in res:
            if callable(callback):
                callback(line, res['Result'])
                print(res['Result'])
          

        if 'ToExchange' in res:
            print(res.get('ToExchange'))
        