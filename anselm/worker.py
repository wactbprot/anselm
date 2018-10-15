import time
import requests
import json
from anselm.system import System
from _thread import start_new_thread


class Worker(System):
    def __init__(self):
        super().__init__()
        self.work_on_line = None
        relay_dict = self.config.get('relay')
        self.relay_dict = relay_dict
        self.relay_url = "http://{}:{}".format(relay_dict.get('host'), relay_dict.get('port'))
        self.headers = {'content-type': 'application/json'}

    def get_worker(self, task, line):
        worker = None
        acc = task['Action']

        if acc == "TCP" or acc == "VXI11" or  acc == "MODBUS":
            worker =  self.relay_worker       
        if acc == "wait":
            worker =  self.wait_worker                   
        
        return worker

    def run(self):
        """The member workonline is set ba anselm
        before the thread is start.
        """
        if self.work_on_line:
            line = self.work_on_line
            task = self.dget('task', line)

            worker = self.get_worker(task, line)
            if worker:
                start_new_thread( worker, (task, line))
            else:
                self.log.error("missing worker function")
                
            self.work_on_line = None
        else:
            self.log.error("member var: work_on_line not set")

    def relay_worker(self, task, line):
       
        req = requests.post(self.relay_url, data=json.dumps(task), headers = self.headers)
        res = req.json()

        if 'DocPath' in task:
            self.aset('doc_path', line,  task['DocPath'], expire=False)

        if 'Result' in res:
            self.aset('result', line,  res['Result'], expire=False)

        if 'ToExchange' in res:
            self.aset('exchange', line, res['ToExchange'], expire=False)

        self.log.debug("values written")
        self.r.publish('io', line)

       

    def wait_worker(self, task, line):
        time.sleep(5)
        self.aset('result', line,  [{'completed':True}], expire=True)
        self.r.publish('io', line)
