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
                            ] })

@app.route('/cal_ids')
def calids():
    keys = s.r.keys('calid@*')
    calids = []
    for key in keys:
        calids.append(s.r.get(key))

    s.log.info("request cal ids")
    
    return jsonify({"ids":calids })

@app.route('/dut_max', methods=['GET'])
def dut_max():
    s.log.info("request max values for dut branchs")
    
    res =   {
             "Dut_A": {
                     "Value": 0.0,
                     "Type": "dut_max_a",
                     "Unit": "Pa"
                 },
             "Dut_B": {
                     "Value": 0.0,
                     "Type": "dut_max_b",
                     "Unit": "Pa"
                 },
             "Dut_C": {
                     "Value": 0.0,
                     "Type": "dut_max_c",
                     "Unit": "Pa"
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
    res = {
            "Pressure_target": {
                         "Caption": "target pressure",
                         "Selected": "1",
                         "Select": []
            }
        }
    keys = s.r.keys('calid@*')
    target_pressure_values = []
    target_pressure_unit = "Pa"
    for key in keys:
        calid = s.r.get(key)
        caldoc = db.get_doc(calid)
        
        todo_pressure = caldoc.get('Calibration', {}).get('ToDo',{}).get('Values',{}).get('Pressure')

        if todo_pressure:
            if todo_pressure.get('Unit') == "mbar":
                conv_factor = 100

            if todo_pressure.get('Unit') == "Pa":
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
                res['Pressure_target']['Selected'] = formated_val
                first = False

            res['Pressure_target']['Select'].append({'value':formated_val , 'display': "{} Pa".format( formated_val) })
    else:
        msg = "no target values found"
        s.log.error(msg)
        res['error'] = msg

    if not 'error' in res:
        return jsonify({'ToExchange':res})
    else:
        return jsonify(res)

@app.route('/offset_sequences', methods=['GET'])
def offset_sequences():
    s.log.info("request to target pressures")
    keys = s.r.keys('offset_all_sequence@*')
    delay = 0.5 #s
    work_count = 0
    for key in keys:
        _ , line = key.split(s.keysep)
        time.sleep(delay)
        sequence = s.dget('offset_all_sequence', line)
        work_count = work_count + len(sequence) -1
        start_new_thread( work_seqence, (sequence, line,))
     
    s.p.subscribe("srv")
    s.log.info('start listening redis ')
    for item in s.p.listen():
        s.log.debug("received item: {}".format(item))
        if item['type'] == 'message':
            s.log.debug(item['data'])
            work_count = work_count -1
            s.log.info("remaining tasks: {}".format(work_count))

            if work_count == 0:
                break
    
    return jsonify({'ok':True, })


def work_seqence(sequence, line):
    worker = Worker()
    delay = 0.2 #s
    for task_name in sequence:
        db.choose_task(task_name, line)
        s.log.debug("choose {} in line {}, start working on".format(task_name, line))
        task = s.dget("task", line)
        worker_fn = worker.get_worker(task, line)
        worker_fn(task, line)
        time.sleep(delay)
        s.r.publish('srv', line)
        