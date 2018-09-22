from flask import Flask, jsonify, request
from anselm.system import System
from anselm.db import DB
from anselm.worker import Worker
from _thread import start_new_thread
import time

app = Flask(__name__)
s = System()
db = DB()

@app.route('/')
def home():
    return jsonify({"routes":[
                                "/cal_ids",
                                "/dut_max",
                                "/target_pressures",
                                "/offset_sequences"
                                "/offset",
                                "/ind"
                            ] })

@app.route('/cal_ids')
def calids():
    keys = s.get_keys('cal_id')
    cal_ids = []
    for key in keys:
        cal_ids.append(s.r.get(key))

    s.log.info("request cal ids")
    
    return jsonify({"ids":cal_ids })

@app.route('/dut_max', methods=['GET'])
def dut_max():
    s.log.info("request max values for dut branchs")
    
    res =   {
             "Dut_A": {
                     "Value": 0.0,
                     "Type": "dut_max_a",
                     "Unit": s.unit
                 },
             "Dut_B": {
                     "Value": 0.0,
                     "Type": "dut_max_b",
                     "Unit": s.unit
                 },
             "Dut_C": {
                     "Value": 0.0,
                     "Type": "dut_max_c",
                     "Unit": s.unit
                 }
             }
    keys = s.r.keys('calid@*')
    for key in keys:
        calid = s.r.get(key)
        _ , line = key.split(s.keysep)

        fullscale_value = s.fget("fullscale_value", line)
        fullscale_unit = s.aget("fullscale_unit", line)        
        dut_branch = s.aget("dut_branch", line)

        if calid and fullscale_value and dut_branch:

            if dut_branch == "dut_a" and res.get('Dut_A').get('Value') < fullscale_value:
                res['Dut_A']['Value'] = fullscale_value
                res['Dut_A']['Unit'] = fullscale_unit

            if dut_branch == "dut_b" and res.get('Dut_B').get('Value') < fullscale_value:
                res['Dut_B']['Value'] = fullscale_value
                res['Dut_B']['Unit'] = fullscale_unit

            if dut_branch == "dut_c" and res.get('Dut_C').get('Value') < fullscale_value:
                res['Dut_C']['Value'] = fullscale_value
                res['Dut_C']['Unit'] = fullscale_unit
              
        else:
            msg = "missing setup for {}".format(calid)
            res['error'] = msg
            s.log.error(msg)
            break

    if not 'error' in res:
        return jsonify({'ToExchange':res})
    else:
        return jsonify(res)

@app.route('/target_pressures', methods=['GET'])
def target_pressure():
    s.log.info("request to target pressures")
    keys = s.r.keys('cal_id@*')
    target_pressure_values = []
  
    res = {
            "Target_pressure": {
                         "Caption": "target pressure",
                         "Unit": s.unit,
                         "Selected": "1",
                         "Select": []
            }
        }
    for key in keys:
        calid = s.r.get(key)
        caldoc = db.get_doc(calid)
        
        todo_pressure = caldoc.get('Calibration', {}).get('ToDo',{}).get('Values',{}).get('Pressure')

        if todo_pressure:
            if todo_pressure.get('Unit') == "mbar":
                conv_factor = 100

            if todo_pressure.get('Unit') == s.unit:
                conv_factor = 1

            for v in todo_pressure.get('Value'):
                val = float(v) * conv_factor
                if not val in  target_pressure_values:
                    target_pressure_values.append(val)
       
        else:
            s.log.warn("calibration {} contains no target pressures".format(calid))

    if len(target_pressure_values) > 0:
        first = True

        for v in sorted(target_pressure_values):
            formated_val = '{:.1e}'.format(v) 
            if first:
                res['Target_pressure']['Selected'] = formated_val
                res['Target_pressure']['Unit'] = s.unit
                first = False

            res['Target_pressure']['Select'].append({'value':formated_val , 'display': "{} {}".format( formated_val, s.unit) })
    else:
        msg = "no target values found"
        s.log.error(msg)
        res['error'] = msg

    if not 'error' in res:
        return jsonify({'ToExchange':res})
    else:
        return jsonify(res)

@app.route('/offset_sequences', methods=['GET','POST'])
def offset_sequences():
    s.log.info("request to offset sequence")
    keys = s.r.keys('offset_all_sequence@*')
    seq_array = []
    for key in keys:
        _ , line = key.split(s.keysep)
        sequence = s.dget('offset_all_sequence', line)
        for task in sequence:
            seq_array.append("{}-{}".format(task.get('TaskName'), line)) 

        start_new_thread( work_seqence, (sequence, line,))
    
    res = wait_sequences_complete(seq_array)

    return jsonify(res)

@app.route('/offset', methods=['POST'])
def offset():
    res = {"ok":True}
    s.log.info("request to endpoint /offset")
    req = request.get_json()

    s.log.debug("receive request with body {}".format(req))
    if 'Target_pressure_value' in req and 'Target_pressure_unit' in req:
        seq_array = []
        target_value = float(req.get('Target_pressure_value'))
        target_unit = req.get('Target_pressure_unit')

        if target_unit == s.unit:
            fs_val_keys = s.r.keys('fullscale_value@*')
           
            for key in fs_val_keys:
                _, line = key.split(s.keysep)
                fullscale_value = s.fget('fullscale_value', line)
                s.log.debug("fullscale value for line {} is {}. Target value is: {}.".format(line, fullscale_value, target_value))

                if target_value < fullscale_value:
                    auto_init_tasks = s.dget('auto_init_tasks', line)
                    s.log.debug("found {} auto init tasks".format(len(auto_init_tasks)))
                    offset_sequence = []
                    for task in auto_init_tasks:                        
                        if 'From' in task and 'To' in task and target_value >= task.get('From') and target_value < task.get('To'):
                            s.log.debug("append for execution task: {} ".format(task))
                            offset_sequence.append(task)
                            seq_array.append("{}-{}".format(task.get('TaskName'), line))

                    # append the offset task
                    offset_task = s.dget("offset_task", line)
                    if  offset_task and 'TaskName' in task:
                        offset_task_name = offset_task.get('TaskName')
                        offset_sequence.append(offset_task)
                        seq_array.append("{}-{}".format(offset_task_name, line))
                    else:
                        offset_sequence = []

                    if len(offset_sequence) >0:
                        start_new_thread( work_seqence, (offset_sequence, line,))
                    else:
                        s.log.info("No task match for line {}".format(line))

            if len(seq_array) > 0:
                res = wait_sequences_complete(seq_array)
            else:
                s.log.info("nothing started")
        else:
            msg = "wrong target unit"
            s.log.error(msg)
            res = {'error':msg}
    else:
        msg = "missing request data (Target_pressure_value or Target_pressure_unit)"
        s.log.error(msg)
        res = {'error' : msg}
   
    return jsonify(res)

@app.route('/ind', methods=['POST'])
def ind():
    res = {"ok":True}
    s.log.info("request to endpoint /ind")
    req = request.get_json()

    s.log.debug("receive request with body {}".format(req))
    if 'Target_pressure_value' in req and 'Target_pressure_unit' in req:
        seq_array = []
        target_value = float(req.get('Target_pressure_value'))
        target_unit = req.get('Target_pressure_unit')

        if target_unit == s.unit:
            fs_val_keys = s.r.keys('fullscale_value@*')
           
            for key in fs_val_keys:
                _, line = key.split(s.keysep)
                fullscale_value = s.fget('fullscale_value', line)
                s.log.debug("fullscale value for line {} is {}. Target value is: {}.".format(line, fullscale_value, target_value))

                if target_value < fullscale_value:
                    auto_init_tasks = s.dget('auto_init_tasks', line)
                    s.log.debug("found {} auto init tasks".format(len(auto_init_tasks)))
                    ind_sequence = []
                    for task in auto_init_tasks:                        
                        if 'From' in task and 'To' in task and target_value >= task.get('From') and target_value < task.get('To'):
                            s.log.debug("append for execution task: {} ".format(task))
                            ind_sequence.append(task)
                            seq_array.append("{}-{}".format(task.get('TaskName'), line))

                    # append the ind task
                    ind_task = s.dget("ind_task", line)
                    if  ind_task and 'TaskName' in task:
                        ind_task_name = ind_task.get('TaskName')
                        ind_sequence.append(ind_task)
                        seq_array.append("{}-{}".format(ind_task_name, line))
                    else:
                        ind_sequence = []

                    if len(ind_sequence) >0:
                        start_new_thread( work_seqence, (ind_sequence, line,))
                    else:
                        s.log.info("No task match for line {}".format(line))

            if len(seq_array) > 0:
                res = wait_sequences_complete(seq_array)
            else:
                s.log.info("nothing started")
        else:
            msg = "wrong target unit"
            s.log.error(msg)
            res = {'error':msg}
    else:
        msg = "missing request data (Target_pressure_value or Target_pressure_unit)"
        s.log.error(msg)
        res = {'error' : msg}
   
    return jsonify(res)

def wait_sequences_complete(seq_array):
    """``seq_array`` is an array of strings. 
    This strings have the form <TaskName>-<Line>. 
    If the task with the name <TaskName> 
    belonging to <line> is completed, the worker publishes 
    the <TaskName>-<Line> string to the ``srv`` channel.
    """
    s.p.subscribe("srv")
    s.log.info('start listening redis on channel srv')
    for item in s.p.listen():
        s.log.debug("received item: {}".format(item))
        if item['type'] == 'message':
            task_element_completed = item.get('data')
            seq_array.remove(task_element_completed)
            if len(seq_array) == 0:
                s.log.info("wait_sequences_complete function will return, all done!")
                break
            else:
                s.log.info("remaining tasks elements: {}".format(seq_array))


    return {'ok':True}

def work_seqence(sequence, line):
    worker = Worker()
    delay = 0.2 #s
    for task in sequence:
        defaults = s.dget('defaults', line)
        if defaults:
            task = db.replace_defaults(task, defaults)
            s.log.debug("defaults: {}".format(defaults))
            s.log.debug("task: {}".format(task))

      
        worker_fn = worker.get_worker(task, line)
        time.sleep(delay)
        worker_fn(task, line)
        data =  "{}-{}".format(task.get('TaskName'), line)
        s.log.debug("will publish to srv for data {}".format(data))
        s.r.publish('srv', data)
        