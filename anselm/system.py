import json
import coloredlogs
import logging
import datetime
import time



class System:
    """
    """
    max_arg_len = 40
    log_fmt = '%(asctime)s,%(msecs)03d %(hostname)s %(filename)s:%(lineno)s %(levelname)s %(message)s'
    log_level = "DEBUG"
    state = {}
    def __init__(self):
        """
        Gets the configuration out of the file: ``config.json``.
        Initializes log system
        """
        # open and parse config file
        with open('anselm/config.json') as json_config_file:
            self.config = json.load(json_config_file)
        self.init_log() 
    
    def init_log(self):
        log_level = self.config.get('loglevel')
        self.log = logging.getLogger()
        
        if log_level is None:
            log_level = self.log_level

        coloredlogs.install(fmt=self.log_fmt, level=log_level, logger=self.log)
   
    def now(self):
        return datetime.datetime.now().isoformat().replace('T', ' ')
