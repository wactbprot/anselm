import json
import pika
import coloredlogs
import logging
import datetime


class System:
    """
    """
    max_arg_len = 40
    log_fmt = '%(asctime)s,%(msecs)03d %(hostname)s %(filename)s:%(lineno)s %(levelname)s %(message)s'

    def __init__(self):
        """
        Gets the configuration out of the file: ``config.json``.
        Initializes log system
        """
        # open and parse config file
        with open('anselm/config.json') as json_config_file:
            self.config = json.load(json_config_file)

        self.init_log()
        self.msg_param = pika.ConnectionParameters(
            host=self.config['rabbitmq']['host'])
        self.log.info("system __init__ complete")

    def init_log(self):
        self.log = logging.getLogger()
        coloredlogs.install(
            fmt=self.log_fmt, level=self.config["loglevel"], logger=self.log)

        self.log.info("logging system online")

    def connection_off(self):
        print("------------------")
        print("------------------")
        print("------------------")
        print("------------------")

    def queue_factory(self, queue_name):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.queue_declare(queue=queue_name)

        return conn, chan

    def init_stm_msg_prod(self):
        conn, chan = self.queue_factory(queue_name='stm')
        self.stm_conn = conn
        self.stm_chan = chan

    def init_ltm_msg_prod(self):
        conn, chan = self.queue_factory(queue_name='ltm')
        self.ltm_conn = conn
        self.ltm_chan = chan

    def init_ltm_msg_consume(self):
        queue_name = 'ltm'
        conn, chan = self.queue_factory(queue_name=queue_name)
        chan.basic_consume(self.dispatch,
                           queue=queue_name,
                           no_ack=True)
        chan.start_consuming()

    def init_stm_msg_consume(self):
        queue_name = 'stm'
        conn, chan = self.queue_factory(queue_name=queue_name)
        chan.basic_consume(self.dispatch,
                           queue=queue_name,
                           no_ack=True)
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
