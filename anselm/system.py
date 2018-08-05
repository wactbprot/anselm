"""brings all systems up and running"""

import json
import pika
import coloredlogs, logging
import datetime

class System:
    """
    """
    max_arg_len = 40
    def __init__(self):
        """
        Gets the configuration out of the file: ``config.json``.
        Initializes log system
        """
        # open and parse config file
        with open('anselm/config.json') as json_config_file:
            config = json.load(json_config_file)

        self.config = config
        self.init_log()
        msg_dict = self.config['rabbitmq']
        self.msg_param = pika.ConnectionParameters(host=msg_dict['host'])

    def init_log(self):
        logger = logging.getLogger()
        fmt = '%(asctime)s,%(msecs)03d %(hostname)s %(filename)s:%(lineno)s %(levelname)s %(message)s'

        coloredlogs.install(
            fmt=fmt, level=self.config["loglevel"], logger=logger)

        self.log = logger
        self.log.info("logging system online")

    def init_stm_msg_prod(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.queue_declare(queue='stm')
        self.stm_conn = conn
        self.stm_chan = chan

    def init_ltm_msg_prod(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.queue_declare(queue='ltm')
        self.ltm_conn = conn
        self.ltm_chan = chan

    def init_ltm_msg_consume(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.queue_declare(queue='ltm')
        chan.basic_consume(self.dispatch,
                           queue='ltm',
                           no_ack=True)

        chan.start_consuming()

    def init_stm_msg_consume(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.queue_declare(queue='stm')
        chan.basic_consume(self.dispatch,
                           queue='stm',
                           no_ack=True)
        self.log.info("short-term memory system start consuming")
        chan.start_consuming()

    def stm_pub(self, body_dict):
        self.stm_chan.basic_publish(exchange='',
                                    routing_key='stm',
                                    body=json.dumps(body_dict))

    def ltm_pub(self, body_dict):
        self.ltm_chan.basic_publish(exchange='',
                                    routing_key='ltm',
                                    body=json.dumps(body_dict))

    def now(self):
        return datetime.datetime.now().isoformat().replace('T', ' ')
