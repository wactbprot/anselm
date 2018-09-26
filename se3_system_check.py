import coloredlogs
import logging
import requests
import json
import redis

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

    log.info("{:*<50}".format("check redis connection"))
    res = rs.client_list()
    if res:
        log.info("{:>50}".format("redis [ok]"))
    else:
        log.error("{:>50}".format("redis [fail]"))

    log.info("{:*<50}".format("check relayServer"))
    data = {'Action': '_version'}
    req = requests.post("http://{}:{}/_version".format(relay.get("host"), relay.get("port")), data=json.dumps(data))
    res = req.json()
    if 'Result' in res:
        log.info("{:>50}".format("relayServer [ok]"))
    else:
        log.error("{:>50}".format("relayServer [fail]"))

    log.info("{:*<50}".format("check database"))
    req = requests.get("http://{}:{}/{}".format(db.get("host"), db.get("port"), db.get("database")))
    res = req.json()

    if 'db_name' in res:
        log.info("{:>50}".format("database [ok]"))
    else:
        log.error("{:>50}".format("database [fail]"))

    log.info("{:*<50}".format("check valves mpd"))
    req = requests.get("http://{}:{}/{}/meta".format(ssmp.get("host"), ssmp.get("port"), ssmp.get("mpd_valves_id")))
    res = req.json()
    if 'id' in res:
        log.info("{:>50}".format("valves mp [ok]"))
    else:
        log.error("{:>50}".format("valves mp [fail]"))

    log.info("{:*<50}".format("check servo mpd"))
    req = requests.get("http://{}:{}/{}/meta".format(ssmp.get("host"), ssmp.get("port"), ssmp.get("mpd_servo_id")))
    res = req.json()
    if 'id' in res:
        log.info("{:>50}".format("servo mp [ok]"))
    else:
        log.error("{:>50}".format("servo mp [fail]"))



if __name__ == '__main__':
   main()