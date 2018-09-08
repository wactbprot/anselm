import requests
import json
from anselm.system import System


class Worker(System):
    work_on_line = None
    def __init__(self):
        super().__init__()
        relay_dict = self.config['relay']
        self.relay_dict = relay_dict
        self.relay_url = "http://{}:{}".format(relay_dict['host'], relay_dict['port'])
        self.headers = {'content-type': 'application/json'}
        

    def run(self):
        """The memeber workomline is set ba anselm
        before the thread is start.
        """
        if self.work_on_line:
            line = self.work_on_line
            task = self.dget('task', line)

            acc = task['Action']

            if acc == "TCP":
                self.relay_worker(task, line)
            if acc == "VXI11":
                self.relay_worker(task, line)
        
            self.work_on_line = None
        else:
            self.log.error("member work_on_line not set")

    def relay_worker(self, task, line):
        req = requests.post(self.relay_url, data=json.dumps(task), headers = self.headers)
        res = req.json()
        print(res)
        if 'Result' in res:
            self.aset('result', line,  res['Result'])
            
          
        if 'ToExchange' in res:
            self.aset('exchange', line, res['ToExchange'])
            
        self.r.publish('io', line)
        
       