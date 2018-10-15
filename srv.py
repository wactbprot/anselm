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
                               {"route": "/cal_ids", "method":['GET']},
                               {"route": "/target_pressure", "method":['GET', 'POST'],"data":['DocPath']},
                               {"route": "/dut_max","method":['GET', 'POST'],"data":['Target_pressure_value', "Target_pressure_unit"]},
                               {"route": "/save_dut_branch","method":['POST'],"data":['DocPath']},
                               {"route": "/save_maintainer","method":['POST'],"data":['DocPath']},
                               {"route": "/save_gas","method":['POST'],"data":['DocPath']},
                               {"route": "/target_pressures","method":['GET']},
                               {"route": "/offset_sequences","method":['GET','POST'],"data":['DocPath']},
                               {"route": "/offset","method":['POST'],"data":['Target_pressure_value', "Target_pressure_unit"]},
                               {"route": "/ind","method":['POST'],"data":['Target_pressure_value', "Target_pressure_unit"]},
                            ] })

@app.route('/cal_ids', methods=['GET'])
def calids():
    msg = "http request to endpoint /cal_ids"
    s.log.info(msg) 
    s.r.publish('info', msg)

    keys = s.get_keys('cal_id')
    cal_ids = []
    for key in keys:
        cal_ids.append(s.r.get(key))

    s.log.info("request cal ids and Exchange")

    return jsonify({"ids":cal_ids, 'ToExchange':{"Ids": ";".join(cal_ids)}})

@app.route('/target_pressure', methods=['GET', 'POST'])
def target_pressure():
    msg = "http request to /target_pressure endpoint"
    s.log.info(msg) 
    s.r.publish('info', msg)

    if request.method == 'POST':
        s.aset('save', 0,  "yes" )
    
    req = request.get_json()
    last_pressure = 0
    lines = s.get_lines('cal_id')
    todo_pressures_acc = []
    for line in lines:
        cal_id = s.aget('cal_id', line)
        doc = db.get_doc(cal_id)

        todo_pressures_acc, todo_unit =  db.acc_todo_pressure(todo_pressures_acc, doc, s.unit)
        test_pressure, test_unit = db.get_last_target_pressure(doc)
        
        if  test_pressure >  last_pressure and  test_unit == s.unit:
            last_pressure = test_pressure
       
    for todo_pressure in  todo_pressures_acc:
        if float(todo_pressure) > last_pressure:
            break
        
    if 'DocPath' in req:
        doc_path = req.get('DocPath')
        for line in lines:
            s.aset("result", line, [{'Type':'target_pressure', 'Value': float(todo_pressure), 'Unit':todo_unit}])
            s.aset("doc_path", line, doc_path)
            db.save_results()
    else:
        msg = "missing DocPath"
        res['error'] = msg
        s.log.error(msg)

    s.aset('save', 0,  "no" )
    s.log.info("check calibration {}".format(cal_id))
    
    return jsonify({'ToExchange':{'Target_pressure.Selected':  float(todo_pressure) , 'Target_pressure.Unit': todo_unit }})

@app.route('/save_dut_branch', methods=['POST'])
def save_dut_branch():
    msg = "http  request to endpoint /save_dut_branch"
    s.log.info(msg) 
    s.r.publish('info', msg)

    if request.method == 'POST':
        s.aset('save', 0,  "yes" )

    s.log.info("request and save dut branch")
    res = {"ok":True}
    req = request.get_json()
    
    if 'DocPath' in req:
        doc_path = req.get('DocPath')
        lines = s.get_lines("cal_id")
        for line in lines:
            s.aset("result", line, [s.aget("dut_branch", line)])
            s.aset("doc_path", line, doc_path)
            db.save_results()
    else:
        msg = "missing DocPath"
        res['error'] = msg
        s.log.error(msg)

    s.aset('save', 0,  "no" )
    return jsonify(res)

@app.route('/save_maintainer', methods=['POST'])
def save_maintainer():
    msg = "http request to endpoint /save_maintainer"
    s.log.info(msg) 
    s.r.publish('info', msg)

    if request.method == 'POST':
        s.aset('save', 0,  "yes" )

    res = {"ok":True}
    req = request.get_json()
    
    if 'DocPath' in req:
        doc_path = req.get('DocPath')
        lines = s.get_lines("cal_id")
        for line in lines:
            s.aset("result", line, [s.aget("maintainer", 0)])
            s.aset("doc_path", line, doc_path)
            db.save_results()
    else:
        msg = "missing DocPath"
        res['error'] = msg
        s.log.error(msg)

    s.aset('save', 0,  "no" )
    if not 'error' in res:
        return jsonify({'ToExchange':{'Maintainer': s.aget("maintainer", 0)}})
    else:
        return jsonify(res)

@app.route('/save_gas', methods=['POST'])
def save_gas():
    msg = "request to endpoint /save_gas"
    s.log.info(msg) 
    s.r.publish('info', msg)

    if request.method == 'POST':
        s.aset('save', 0,  "yes" )

    res = {"ok":True}
    req = request.get_json()
    
    if 'DocPath' in req:
        doc_path = req.get('DocPath')
        lines = s.get_lines("cal_id")
        for line in lines:
            s.aset("result", line, [s.aget("gas", 0)])
            s.aset("doc_path", line, doc_path)
            db.save_results()
    else:
        msg = "missing DocPath"
        res['error'] = msg
        s.log.error(msg)

    s.aset('save', 0,  "no" )
    if not 'error' in res:
        return jsonify({'ToExchange':{'Gas': s.aget("gas", 0)}})
    else:
        return jsonify(res)


@app.route('/dut_max', methods=['GET', 'POST'])
def dut_max():
    msg = "http request to endpoint /dut_max"
    s.log.info(msg) 
    s.r.publish('info', msg)

    if request.method == 'POST':
        s.aset('save', 0,  "yes" )
        req = request.get_json()
        s.log.debug("receive request with body {}".format(req))
    
    if 'Target_pressure_value' in req and 'Target_pressure_unit' in req:
        target_value = float(req.get('Target_pressure_value'))
        target_unit = req.get('Target_pressure_unit')
    else:
         target_value = 0
         target_unit = "Pa"
           
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
                 },
            "Set_Dut_A": "close",
            "Set_Dut_B": "close",
            "Set_Dut_C": "close"
            }
    lines = s.get_lines('cal_id')
    # loop over all devices on every branch
    for line in lines:
        fullscale_value = s.fget("fullscale_value", line)
        fullscale_unit = s.aget("fullscale_unit", line)        
        dut_branch = s.aget("dut_branch", line)

        if  fullscale_value and dut_branch:

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
            msg = "missing setup for line {}".format(line)
            res['error'] = msg
            s.log.error(msg)
            break

    if not 'error' in res and request.method == 'POST' and target_value > 0 and fullscale_unit == target_unit:
        if  target_value > res['Dut_A']['Value']:
            res['Set_Dut_A'] = "close"
        else:
            res['Set_Dut_A'] = "open"
        
        if  target_value > res['Dut_B']['Value']:
            res['Set_Dut_B'] = "close"
        else:
            res['Set_Dut_B'] = "open"
        
        if  target_value > res['Dut_C']['Value']:
            res['Set_Dut_C'] = "close"
        else:
            res['Set_Dut_C'] = "open"
    
    if 'DocPath' in req:
        doc_path = req.get('DocPath')
        lines = s.get_lines("cal_id")
        for line in lines:
            s.aset("result", line, [{'Type':'dut_a',  'Value':res['Set_Dut_A']}, 
                                    {'Type':'dut_b',  'Value':res['Set_Dut_B']}, 
                                    {'Type':'dut_c',  'Value':res['Set_Dut_C']}])
            s.aset("doc_path", line, doc_path)   
            s.log.debug("start save dut positions")
            db.save_results()

    if not 'error' in res:
        return jsonify({'ToExchange':res})
    else:
        return jsonify(res)

@app.route('/target_pressures', methods=['GET'])
def target_pressures():
    msg = "http request to endpoint /target_pressures"
    s.log.info(msg) 
    s.r.publish('info', msg)
   
    res = {
            "Target_pressure": {
                         "Caption": "target pressure",
                         "Unit": s.unit,
                         "Selected": "1",
                         "Select": []
            }
        }

    target_pressure = []
    lines = s.get_lines('cal_id')
    for line in lines:

        cal_id = s.aget('cal_id', line)
        doc = db.get_doc(cal_id)
        target_pressure, unit = db.acc_todo_pressure(doc=doc, acc=target_pressure, unit=s.unit)

    if len(target_pressure) > 0:
        for value in target_pressure:
            res['Target_pressure']['Select'].append({'value':value , 'display': "{} {}".format( value, s.unit) })

        res['Target_pressure']['Selected'] = target_pressure[0]
        res['Target_pressure']['Unit'] = s.unit
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
    msg = "request to endpoint /offset_sequences"
    s.log.info(msg) 
    s.r.publish('info', msg)
   
    if request.method == 'POST':
        s.aset('save', 0,  "yes" )

    s.log.info("request to offset sequence")
    lines = s.get_lines('offset_all_sequence')
    seq_array = []
    for line in lines:
        sequence = s.dget('offset_all_sequence', line)
         
        for task in sequence:
            seq_array.append("{}-{}".format(task.get('TaskName'), line)) 

        start_new_thread( work_seqence, (sequence, line,))
    
    res = wait_sequences_complete(seq_array)

   
    return jsonify(res)

@app.route('/offset', methods=['POST'])
def offset():
    msg = "request to endpoint /offset"
    s.log.info(msg) 
    s.r.publish('info', msg)

    s.aset('save', 0,  "yes" )
    res = {"ok":True}
    req = request.get_json()

    s.log.debug("receive request with body {}".format(req))

    if 'Target_pressure_value' in req and 'Target_pressure_unit' in req:
        seq_array = []
        target_value = float(req.get('Target_pressure_value'))
        target_unit = req.get('Target_pressure_unit')

        if target_unit == s.unit:

            lines = s.get_lines('fullscale_value')
            for line in lines:
                fullscale_value = s.fget('fullscale_value', line)
                s.log.debug("fullscale value for line {} is {}. Target value is: {}.".format(line, fullscale_value, target_value))

                if target_value < fullscale_value:
                    offset_sequence = []
                    
                    auto_init_task = select_task(target_value, s.dget('auto_init_tasks', line))
                    if auto_init_task is not None:
                        seq_array.append("{}-{}".format(auto_init_task.get('TaskName'), line))
                        offset_sequence.append(auto_init_task)

                    offset_task = select_task(target_value,  s.dget('offset_tasks', line))
                    if offset_task is not None:
                        seq_array.append("{}-{}".format(offset_task.get('TaskName'), line))
                        offset_sequence.append(offset_task)
                    
                    
                if len(offset_sequence) >0:
                    start_new_thread( work_seqence, (offset_sequence, line,))
                else:
                    s.log.info("No task match for line {}".format(line))
                    s.log.info("nothing started")

            res = wait_sequences_complete(seq_array)
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
    msg = "request to endpoint /ind"
    s.log.info(msg) 
    s.r.publish('info', msg)
    s.aset('save', 0,  "yes" )
    res = {"ok":True}
    req = request.get_json()

    s.log.debug("receive request with body {}".format(req))

    if 'Target_pressure_value' in req and 'Target_pressure_unit' in req:
        seq_array = []
        target_value = float(req.get('Target_pressure_value'))
        target_unit = req.get('Target_pressure_unit')

        if target_unit == s.unit:

            lines = s.get_lines('fullscale_value')
            for line in lines:
                fullscale_value = s.fget('fullscale_value', line)
                s.log.debug("fullscale value for line {} is {}. Target value is: {}.".format(line, fullscale_value, target_value))

                if target_value < fullscale_value:
                    ind_sequence = []
                    
                    auto_init_task = select_task(target_value, s.dget('auto_init_tasks', line))
                    if auto_init_task is not None:
                        seq_array.append("{}-{}".format(auto_init_task.get('TaskName'), line))
                        ind_sequence.append(auto_init_task)

                    ind_task = select_task(target_value, s.dget('ind_tasks', line))
                    if ind_task is not None:
                        seq_array.append("{}-{}".format(ind_task.get('TaskName'), line))
                        ind_sequence.append(ind_task)
                    
                    
                if len(ind_sequence) >0:
                    start_new_thread( work_seqence, (ind_sequence, line,))
                else:
                    s.log.info("No task match for line {}".format(line))
                    s.log.info("nothing started")
            res = wait_sequences_complete(seq_array)
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

def select_task(target_pressure, task_array):
    res = None
    for task in task_array:
        if 'From' in task and 'To' in task:
            if target_pressure >= task.get('From') and target_pressure <= task.get('To'):
                res = task
                break
        else:
            res = task
            break

    return res