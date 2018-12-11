from flask import Flask, jsonify, request
from anselm.system import System
from anselm.db import DB
from anselm.worker import Worker
from anselm.utils import Utils
from _thread import start_new_thread
import time

app = Flask(__name__)
s = System()
db = DB()
utils = Utils()

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
    msg = "http request to endpoint */cal_ids*"
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
    msg = "http request to */target_pressure* endpoint"
    s.log.info(msg) 
    s.r.publish('info', msg)
    req = request.get_json()

    # start values:
    last_pressure = 0.0
    repeat_over_rating = 7.0
    continue_measurement = True
    highest_rating = 0 
    todo_pressures_acc = []
    target_pressures_acc = []
    n_todo = []
    n_target = []

    lines = s.get_lines('cal_id')

    for line in lines:
        cal_id = s.aget('cal_id', line)
        doc = db.get_doc(cal_id)

        todo_dict = utils.extract_todo_pressure(doc)
        todo_pressures_acc, n_todo, todo_unit = utils.acc_pressure(value_dict=todo_dict,form_pressure_acc=todo_pressures_acc, n_acc=n_todo)

        last_rating = db.get_last_rating(doc)
        if last_rating and last_rating > highest_rating:
            highest_rating = last_rating

        last_measured_pressure, last_measured_unit = db.get_last_target_pressure(doc)
        if  last_pressure < last_measured_pressure:
            last_pressure = last_measured_pressure
        
    
    target_dict = utils.extract_target_pressure(doc)
    remaining_pressures, remaining_unit =  utils.remaining_pressure(target_dict, todo_pressures_acc, n_todo)
    
   
    measurement_complete = len(remaining_pressures) == 0
    
    if highest_rating < repeat_over_rating:
        
        if not measurement_complete:
            continue_measurement = True
            # next pressure with ok rating
            next_pressure, next_unit = remaining_pressures[0], remaining_unit
            s.r.publish('info', "The previous measurement point has a rating of *{:.1f}* of [0..9].".format(highest_rating))
            s.r.publish('info', "Proceed with the next pressure point.")

            s.r.publish( 'info', "The calibration pressure will be *{} {}*.".format(next_pressure, next_unit))
        else:
            continue_measurement = False
            s.r.publish('info', "The previous measurement point has a rating of *{:.1f}* of [0..9].".format(highest_rating))
            s.r.publish('info', "It was the *last measurement point*.")

    if  highest_rating > repeat_over_rating:
        continue_measurement = True

        # next pressure with ok rating not ok
        next_pressure, next_unit = last_pressure, last_pressure_unit

        s.r.publish('info', "The previous measurement point has a rating of *{:.1f}*. This is *not ok*.".format(highest_rating))
        s.r.publish('info', "Repeat the previous pressure point ")
    
    if continue_measurement:  
        s.aset("current_target_pressure", 0, "{} {}".format(next_pressure, next_unit))
        if 'DocPath' in req:
            doc_path = req.get('DocPath')
            for line in lines:
                if request.method == 'POST':
                    s.aset('save', line,  "yes" )

                s.aset("result", line, [{'Type':'target_pressure', 'Value': float(next_pressure), 'Unit':next_unit}])
                s.aset("doc_path", line, doc_path)
                db.save_results()
        else:
            msg = "missing DocPath"
            res['error'] = msg
            s.log.error(msg)

       
        return jsonify({'ToExchange':{'Target_pressure.Selected':  float(next_pressure) , 'Target_pressure.Unit': next_unit , 'Continue_mesaurement.Bool': continue_measurement}})
    else:
        return jsonify({'ToExchange':{'Continue_mesaurement.Bool': continue_measurement}})   

@app.route('/save_dut_branch', methods=['POST'])
def save_dut_branch():
    msg = "http  request to endpoint */save_dut_branch*"
    s.log.info(msg) 
    s.r.publish('info', msg)

    res = {"ok":True}
    req = request.get_json()
    
    if 'DocPath' in req:
        doc_path = req.get('DocPath')
        lines = s.get_lines("cal_id")
        for line in lines:
            if request.method == 'POST':
                s.aset('save', line,  "yes" )
            
            s.aset("result", line, [s.aget("dut_branch", line)])
            s.aset("doc_path", line, doc_path)
            db.save_results()

    else:
        msg = "missing DocPath"
        res['error'] = msg
        s.log.error(msg)

  
    return jsonify(res)

@app.route('/save_maintainer', methods=['POST'])
def save_maintainer():
    msg = "http request to endpoint */save_maintainer*"
    s.log.info(msg) 
    s.r.publish('info', msg)

    res = {"ok":True}
    req = request.get_json()
    
    if 'DocPath' in req:
        doc_path = req.get('DocPath')
        lines = s.get_lines("cal_id")
        for line in lines:
            if request.method == 'POST':
                s.aset('save', line,  "yes" )
            
            s.aset("result", line, [s.aget("maintainer", 0)])
            s.aset("doc_path", line, doc_path)
            db.save_results()
    else:
        msg = "missing DocPath"
        res['error'] = msg
        s.log.error(msg)

    if not 'error' in res:
        return jsonify({'ToExchange':{'Maintainer': s.aget("maintainer", 0)}})
    else:
        return jsonify(res)

@app.route('/save_gas', methods=['POST'])
def save_gas():
    msg = "http request to endpoint */save_gas*"
    s.log.info(msg) 
    s.r.publish('info', msg)

    res = {"ok":True}
    req = request.get_json()
    
    if 'DocPath' in req:
        doc_path = req.get('DocPath')
        lines = s.get_lines("cal_id")
        for line in lines:
            if request.method == 'POST':
                s.aset('save', line,  "yes" )

            s.aset("result", line, [s.aget("gas", 0)])
            s.aset("doc_path", line, doc_path)
            db.save_results()
    else:
        msg = "missing DocPath"
        res['error'] = msg
        s.log.error(msg)

    if not 'error' in res:
        return jsonify({'ToExchange':{'Gas': s.aget("gas", 0)}})
    else:
        return jsonify(res)


@app.route('/dut_max', methods=['GET', 'POST'])
def dut_max():
    msg = "http request to endpoint */dut_max*"
    s.log.info(msg) 
    s.r.publish('info', msg)
    req = request.get_json()
   
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
    # loop over all devices on every branch
    lines = s.get_lines('cal_id')
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
            if request.method == 'POST':
                s.aset('save', line,  "yes" )
            
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
    msg = "http request to endpoint */target_pressures*"
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
    n=[]
    lines = s.get_lines('cal_id')
    for line in lines:

        cal_id = s.aget('cal_id', line)
        doc = db.get_doc(cal_id) 
        value_dict = utils.extract_todo_pressure(doc)
        print(value_dict)
        target_pressure, n, unit = utils.acc_pressure(value_dict=value_dict,  form_pressure_acc=target_pressure, n_acc=n)

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
    msg = "http request to endpoint */offset_sequences*"
    s.log.info(msg) 
    s.r.publish('info', msg)
    
    seq_array = []
   
    lines = s.get_lines('offset_all_sequence')
    for line in lines:
        if request.method == 'POST':
            s.aset('save', line,  "yes" )
            s.log.debug("set save at line {} to yes".format(line))

        
        sequence = s.dget('offset_all_sequence', line)
         
        for task in sequence:
            seq_array.append("{}-{}".format(task.get('TaskName'), line)) 

        start_new_thread( work_seqence, (sequence, line,))
    
    res = wait_sequences_complete(seq_array)

   
    return jsonify(res)

@app.route('/offset', methods=['POST'])
def offset():
    msg = "http request to endpoint */offset*"
    s.log.info(msg) 
    s.r.publish('info', msg)
    res = {"ok":True}
    req = request.get_json()

    if 'Target_pressure_value' in req and 'Target_pressure_unit' in req:
        seq_array = []
        target_value = float(req.get('Target_pressure_value'))
        target_unit = req.get('Target_pressure_unit')

        if target_unit == s.unit:

            lines = s.get_lines('fullscale_value')
            for line in lines:
                if request.method == 'POST':
                    s.aset('save', line,  "yes" )

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
    msg = "http request to endpoint */ind*"
    s.log.info(msg) 
    s.r.publish('info', msg)
  
    res = {"ok":True}
    req = request.get_json()

    if 'Target_pressure_value' in req and 'Target_pressure_unit' in req:
        seq_array = []
        target_value = float(req.get('Target_pressure_value'))
        target_unit = req.get('Target_pressure_unit')

        if target_unit == s.unit:

            lines = s.get_lines('fullscale_value')
            for line in lines:
                if request.method == 'POST':
                    s.aset('save', line,  "yes" )

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