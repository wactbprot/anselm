import time
import requests
import json
from anselm.system import System
from _thread import start_new_thread


class Worker(System):
    work_on_line = None
    def __init__(self):
        super().__init__()
        relay_dict = self.config['relay']
        self.relay_dict = relay_dict
        self.relay_url = "http://{}:{}".format(relay_dict['host'], relay_dict['port'])
        self.headers = {'content-type': 'application/json'}
        

    def run(self):
        """The member workonline is set ba anselm
        before the thread is start.
        """
        if self.work_on_line:
            line = self.work_on_line
            task = self.dget('task', line)

            acc = task['Action']

            if acc == "TCP" or acc == "VXI11" or  acc == "MODBUS":
                worker =  self.relay_worker   
                
            if acc == "wait":
                worker =  self.wait_worker                   

        
            start_new_thread( worker, (task, line))
            self.work_on_line = None
        else:
            self.log.error("member var: work_on_line not set")

    def relay_worker(self, task, line):
        repeat = True
        while repeat:
            req = requests.post(self.relay_url, data=json.dumps(task), headers = self.headers)
            res = req.json()

            if 'Result' in res:
                self.aset('result', line,  res['Result'], expire=False)

            if 'ToExchange' in res:
                self.aset('exchange', line, res['ToExchange'], expire=False)

            self.log.debug("values written")
            self.r.publish('io', line)

            run_kind = self.aget('run_kind', line)
            self.log.debug("run_kind is {}".format(run_kind))
            if run_kind == 'loop':
                repeat = True
            else:
                repeat = False
                break

    def wait_worker(self, task, line):
        time.sleep(5)
        self.aset('result', line,  [{'completed':True}], expire=True)
        self.r.publish('io', line)









