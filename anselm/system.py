import json
import coloredlogs
import logging
import datetime
import time
import redis

class System:
    """
    """
    expire_time = 10000 #ms
    log_fmt = '%(asctime)s,%(msecs)03d %(hostname)s %(filename)s:%(lineno)s %(levelname)s %(message)s'
    log_level = "DEBUG"
    unit = 'Pa'
    first_item ="select"   
    last_item = "remove"
    keysep = "@"

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

        self.r = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self.log.info("key value store ok")

        self.p = self.r.pubsub()
        self.log.info("pubsub ok")

    def gen_key(self, key_prefix, line):

        return '{}{}{}'.format(key_prefix, self.keysep, line) 

    def get_keys(self, key_prefix):
        
        return self.r.keys("{}{}*".format(key_prefix, self.keysep))
    
    def get_lines(self, key_prefix):
        keys = self.get_keys(key_prefix) 

        return [key.split(self.keysep)[1] for key in keys]
    
    def adelete(self, key_prefix, line):

        k = self.gen_key(key_prefix, line)
        self.r.delete(k)

    def aset(self, key_prefix, line, value, expire=False):

        k = self.gen_key(key_prefix, line)

        if isinstance(value, dict) or isinstance(value, list):
            v = json.dumps(value)
        else:
            v = value

        if v == self.first_item or v == self.last_item:
            self.r.delete(k)
        else:
            self.r.set(k,v)

        if expire:
            self.r.pexpire(k, self.expire_time)

    def aget(self, key_prefix, line):
        """Get the element described by key_prefix and line
        from mem store
        """
        k = self.gen_key(key_prefix, line)
        
        return self.r.get(k)
    
    def dget(self, key_prefix, line):
        """Get a dict from mem store by key_prefix and line
        """
        v = self.aget(key_prefix, line)
        
        if v:
            return json.loads(v)
        else:
            return None

        
    def fget(self, key_prefix, line):
        """Get a float from mem store by key_prefix and line
        """
        v = self.aget(key_prefix, line)
        
        if v:
            return float(v)
        else:
            return None
            
    def now(self):
        return datetime.datetime.now().isoformat().replace('T', ' ')

    