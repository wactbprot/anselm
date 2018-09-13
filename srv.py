from flask import Flask, jsonify, request
from anselm.system import System
from anselm.db import DB
app = Flask(__name__)
s = System()
db = DB()

@app.route('/calids')
def calids():
    keys = s.r.keys('calid@*')
    calids = []
    for key in keys:
        calids.append(s.r.get(key))

    s.log.info("request cal ids")
    
    return jsonify({"calids":calids })

@app.route('/dut_max', methods=['GET'])
def dut_max():
    s.log.info("request max values for dut branchs")
    
    keys = s.r.keys('calid@*')
    res =   {
             "Dut_A": {
                     "Value": 0.0,
                     "Type": "dut_max_a",
                     "Unit": "mbar"
                 },
             "Dut_B": {
                     "Value": 0.0,
                     "Type": "dut_max_b",
                     "Unit": "mbar"
                 },
             "Dut_C": {
                     "Value": 0.0,
                     "Type": "dut_max_c",
                     "Unit": "mbar"
                 }
             }

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
