from flask import Flask, jsonify
from anselm.system import System
app = Flask(__name__)
s = System()

@app.route('/calids')
def calids():
    keys = s.r.keys('calid@*')
    calids = []
    for key in keys:
        calids.append(s.r.get(key))

    s.log.info("request cal ids")
    
    return jsonify({"calids":calids })