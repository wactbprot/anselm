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

@app.route('/setup', methods=['GET', 'PUT', 'POST'])
def setup():
    s.log.info("request setup")
    
    keys = s.r.keys('calid@*')
    calids = []
    fullscales = []
    dut_branches = []
    res = {}
    for key in keys:
        calid = s.r.get(key)
        _ , line = key.split("@")
        fullscale = s.r.get("fullscale@{}".format(line))
        dut_branche = s.r.get("dut_branch@{}".format(line))
        if calid and fullscale and dut_branche:
            calids.append(calid)
            fullscales.append(fullscale)
            dut_branches.append(dut_branche)
        else:
            res['error'] = "missing setup for {}".format(calid)
            break
    if not 'error' in res:
        res['calids'] = calids
        res['fullscales'] = fullscales
        res['dut_branches'] = dut_branches

    if request.method == 'GET':
        return jsonify(res)