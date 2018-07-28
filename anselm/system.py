"""brings all systems up and running"""


import json
import coloredlogs, logging

class System:
    """
    """
    def __init__(self):
        """
        Gets the configuration out of the file: ``config.json``.
        Initializes sub systems
        """
        # open and parse config file
        with open('anselm/config.json') as json_config_file:
            config = json.load(json_config_file)

        self.config = config
        self.init_log()

    def init_log(self):
        logger = logging.getLogger()
        fmt = '%(asctime)s,%(msecs)03d %(hostname)s %(filename)s:%(lineno)s %(levelname)s %(message)s'

        coloredlogs.install(
            fmt=fmt, level=self.config["loglevel"], logger=logger)

        self.log = logger
        self.log.info("logging system online")
