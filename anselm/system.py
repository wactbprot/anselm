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
        self.log = logging.getLogger()
        coloredlogs.install(
            fmt=self.log_fmt, level=self.config["loglevel"], logger=self.log)

        self.log.info("logging system online")

   
    def now(self):
        return datetime.datetime.now().isoformat().replace('T', ' ')
