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
        r = requests.post(self.relay_url, data=json.dumps(task), headers = self.headers)
        print(r.json())