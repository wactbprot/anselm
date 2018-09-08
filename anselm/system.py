import json
import coloredlogs
import logging
import datetime
import time
import redis

class System:
    """
    """
    max_arg_len = 40
    log_fmt = '%(asctime)s,%(msecs)03d %(hostname)s %(filename)s:%(lineno)s %(levelname)s %(message)s'
    log_level = "DEBUG"
   
    def __init__(self):
        """
        Gets the configuration out of the file: ``config.json``.
        Initializes log system
        """
        # open and parse config file
        with open('anselm/config.json') as json_config_file:
            self.config = json.load(json_config_file)
        self.init_log()
        self.init_kv() 
    
    def init_log(self):
    
        log_level = self.config.get('loglevel')
        self.log = logging.getLogger()
        
        if log_level is None:
            log_level = self.log_level

        coloredlogs.install(fmt=self.log_fmt, level=log_level, logger=self.log)
    
    def init_kv(self):
    
        db_dict = self.config.get('redis')
        port = db_dict.get('port')
        host = db_dict.get('host')
        db =  db_dict.get('db')

        self.r = redis.StrictRedis(host=host, port=port, db=db)
        self.log.info("key value store ok")

        self.p = self.r.pubsub()
        self.log.info("pubsub ok")

    def aset(self, key_prefix, line, value):
        k = '{}@{}'.format(key_prefix, line)
        
        if isinstance(value, dict) or isinstance(value, list):
            v = json.dumps(value)

        if isinstance(value, str):
            v = value

        self.r.set(k,v)
    
    def aget(self, key_prefix, line):
        k = '{}@{}'.format(key_prefix, line) 
        
        return self.r.get(k)
    
    def dget(self, key_prefix, line):
        v = self.aget(key_prefix, line)
        
        return json.loads(v)

    def now(self):
        return datetime.datetime.now().isoformat().replace('T', ' ')
