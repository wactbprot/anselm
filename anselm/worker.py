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
        
    def run(self, task):
        acc = task.get('Action')

        if acc:
            if acc == "TCP":
                self.relay_worker(task)
        else:
            self.log.error("task contains no action")

    def relay_worker(self, task):
        req = requests.post(self.relay_url, data=json.dumps(task), headers = self.headers)
        res = req.json()
        
        if 'Result' in res:
            print(res.get('Result'))
            print(self.state)

        if 'ToExchange' in res:
            print(res.get('ToExchange'))
        