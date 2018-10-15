import coloredlogs
import logging
import requests
import json
import redis
import sys

def main():
    with open('anselm/config.json') as json_config_file:
        config = json.load(json_config_file)

    log = logging.getLogger()
    coloredlogs.install( level="INFO", logger=log)
    ssmp = config.get("ssmp")
    db = config.get("couchdb")
    relay = config.get("relay")
    r = config.get("redis")
    rs = redis.StrictRedis(host=r.get("host"), port=r.get("port"), db=r.get("DB"), decode_responses=True)

    # check redis
    log.info("{:*<50}".format("check redis connection"))
    res = rs.client_list()
    if res:
        log.info("{:>50}".format("redis [ok]"))
    else:
        log.error("{:>50}".format("redis [fail]"))
        sys.exit("start redis")

    # check relay server
    log.info("{:*<50}".format("check relayServer"))
    data = {'Action': '_version'}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if 'Result' in res:
        log.info("{:>50}".format("relayServer ({}) [ok]".format(res.get('Result'))))
    else:
        log.error("{:>50}".format("relayServer [fail]"))
        sys.exit("start relay server")
    
    # check ppc4
    log.info("{:*<50}".format("check ppc4 (unit Pa)"))
    data = {'Action': 'TCP', "Host": "e75443", "Port":"5302", "Value":"UNIT\r"}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    
    if "Result" in res and res['Result'] == "Pa  a\r\n":  
        log.info("{:>50}".format("ppc4 [ok]"))
    else:
        log.error("{:>50}".format("ppc4 [fail]"))
        sys.exit("check PPC4 rs232, port 3 at e75443, check unit Pa")

    # check p_fill modbus/CDGs
    log.info("{:*<50}".format("check filling pressure CDGs"))
    data = {'Action': 'MODBUS', "Host": "e75451",  "Address": 0, "Quantity": 48, "FunctionCode": "ReadInputRegisters", "OutMode": "Buffer",}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if "Result" in res and "data" in res['Result'] and len( res['Result']['data']) == 96:  
        log.info("{:>50}".format("filling pressure CDGs [ok]"))
    else:
        log.error("{:>50}".format("filling pressure CDGs [fail]"))
        sys.exit("Modbus e75451")
    
    # check add-vol-cdg/check standard modbus/CDGs
    log.info("{:*<50}".format("check ad. vol. CDG"))
    data = {'Action': 'MODBUS', "Host": "e75480",  "Address": 0, "Quantity": 8, "FunctionCode": "ReadInputRegisters", "OutMode": "Buffer",}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if "Result" in res and "data" in res['Result'] and len( res['Result']['data']) == 16:  
        log.info("{:>50}".format("ad. vol. CDG [ok]"))
    else:
        log.error("{:>50}".format("ad. vol. CDG [fail]"))
        sys.exit("Modbus e75451")
    
    # temperature keithley
    log.info("{:*<50}".format("temperature keithley"))
    data = {'Action': 'VXI11', "Host": "e75440", "Device":"inst0",  "Value": "return_50()\n"}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()

    if "Result" in res and len(res['Result']) == 51:  
        log.info("{:>50}".format("temperature keithley [ok]"))
    else:
        log.error("{:>50}".format("temperature keithley [fail]"))
        sys.exit("configure servos, use mpd-se3-servo")
    
    # check servos
    # node 1
    log.info("{:*<50}".format("check servo node 1 (cont. current)"))
    data = {'Action': 'TCP', "Host": "e75443", "Port":"5301", "Value":"1GCC\r"}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if "Result" in res and float(res['Result']) == 600:  
        log.info("{:>50}".format("node 1 [ok]"))
    else:
        log.error("{:>50}".format("node 1 [fail]"))
        sys.exit("configure servos, use mpd-se3-servo")

    # node 2    
    log.info("{:*<50}".format("check servo node 2 (cont. current)"))
    data = {'Action': 'TCP', "Host": "e75443", "Port":"5300", "Value":"2GCC\r"}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if "Result" in res and float(res['Result']) == 600:  
        log.info("{:>50}".format("node 2 [ok]"))
    else:
        log.error("{:>50}".format("node 2 [fail]"))
        sys.exit("configure servos, use mpd-se3-servo")

    # node 3
    log.info("{:*<50}".format("check servo node 3 (cont. current)"))
    data = {'Action': 'TCP', "Host": "e75443", "Port":"5301", "Value":"3GCC\r"}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if "Result" in res and float(res['Result']) == 600:  
        log.info("{:>50}".format("node 3 [ok]"))
    else:
        log.error("{:>50}".format("node 3 [fail]"))
        sys.exit("configure servos, use mpd-se3-servo")

    # node 4
    log.info("{:*<50}".format("check servo node 4 (cont. current)"))
    data = {'Action': 'TCP', "Host": "e75443", "Port":"5300", "Value":"4GCC\r"}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if "Result" in res and float(res['Result']) == 600:  
        log.info("{:>50}".format("node 4 [ok]"))
    else:
        log.error("{:>50}".format("node 4 [fail]"))
        sys.exit("configure servos, use mpd-se3-servo")
    
    # node 5
    log.info("{:*<50}".format("check servo node 5 (cont. current)"))
    data = {'Action': 'TCP', "Host": "e75443", "Port":"5301", "Value":"5GCC\r"}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if "Result" in res and float(res['Result']) == 600:  
        log.info("{:>50}".format("node 5 [ok]"))
    else:
        log.error("{:>50}".format("node 5 [fail]"))
        sys.exit("configure servos, use mpd-se3-servo")
   
    # node 6    
    log.info("{:*<50}".format("check servo node 6 (cont. current)"))
    data = {'Action': 'TCP', "Host": "e75443", "Port":"5300", "Value":"6GCC\r"}
    req = requests.post("http://{}:{}".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if "Result" in res and float(res['Result']) == 600:  
        log.info("{:>50}".format("node 6 [ok]"))
    else:
        log.error("{:>50}".format("node 6 [fail]"))
        sys.exit("configure servos, use mpd-se3-servo")

    # check vl_db_work
    log.info("{:*<50}".format("check database"))
    req = requests.get("http://{}:{}/{}".format(db.get("host"), db.get("port"), db.get("database")))
    res = req.json()
    if 'db_name' in res:
        log.info("{:>50}".format("database [ok]"))
    else:
        log.error("{:>50}".format("database [fail]"))
        sys.exit("start couchdb, ensure vl_db_work exists")

    # valves mpd
    log.info("{:*<50}".format("check valves mpd"))
    req = requests.get("http://{}:{}/{}/meta".format(ssmp.get("host"), ssmp.get("port"), ssmp.get("mpd_valves_id")))
    res = req.json()
    if 'id' in res:
        log.info("{:>50}".format("valves mp [ok]"))
    else:
        log.error("{:>50}".format("valves mp [fail]"))
        sys.exit("load mpd-se3-valves")

    # servo mpd
    log.info("{:*<50}".format("check servo mpd"))
    req = requests.get("http://{}:{}/{}/meta".format(ssmp.get("host"), ssmp.get("port"), ssmp.get("mpd_servo_id")))
    res = req.json()
    if 'id' in res:
        log.info("{:>50}".format("servo mp [ok]"))
    else:
        log.error("{:>50}".format("servo mp [fail]"))
        sys.exit("load mpd-se3-servo")

    # state mpd
    log.info("{:*<50}".format("check state mpd"))
    req = requests.get("http://{}:{}/{}/meta".format(ssmp.get("host"), ssmp.get("port"), ssmp.get("mpd_state_id")))
    res = req.json()
    if 'id' in res:
        log.info("{:>50}".format("state mp [ok]"))
    else:
        log.error("{:>50}".format("state mp [fail]"))
        sys.exit("load mpd-se3-state")

    # branches closed
    log.info("{:*<50}".format("check all dut branch flanged blind"))
    ok = input("all dut flanges closed? [y|n]: ")
    if ok == "y":
          log.info("{:>50}".format("duts [ok]"))
    else:
        log.error("{:>50}".format("duts [fail]"))
        sys.exit("close dut branches")

    # gas supply
    log.info("{:*<50}".format("check gas supply"))
    ok = input("gas bottel open, pressure ok? [y|n]: ")
    if ok == "y":
          log.info("{:>50}".format("gas supply [ok]"))
    else:
        log.error("{:>50}".format("gas supply [fail]"))
        sys.exit("ensure gas supply")

if __name__ == '__main__':
   main()