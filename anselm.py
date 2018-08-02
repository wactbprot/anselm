import sys
import json
import argparse
import pika
from anselm.system import System
class Anselm(System):
    """
    https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html
    """
    def __init__(self):
        super().__init__()

        msg_dict = self.config['rabbitmq']
        host = msg_dict['host']
        self.msg_param = pika.ConnectionParameters(host=host)

        self.init_ltm_msg_prod()
        self.init_stm_msg_prod()

        parser = argparse.ArgumentParser(
            description='check systems',
            usage='''anselm <command> [<args>]''')

        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command):
            parser.print_help()
            exit(1)

        if len(args.command) > self.max_arg_len:
            print("command too long")
            exit(1)

        getattr(self, args.command)()

    def init_ltm_msg_prod(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.queue_declare(queue='ltm')
        self.ltm_conn = conn
        self.ltm_chan = chan

    def init_stm_msg_prod(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.queue_declare(queue='stm')
        self.stm_conn = conn
        self.stm_chan = chan

    def start(self):
        """
        .. todo::
            find better (more speaking) routing key
        """

        parser = argparse.ArgumentParser(
            description="sends a all to ltm exchange")

        self.ltm_chan.basic_publish(exchange='',
                                    routing_key='ltm',
                                    body=json.dumps({'do':'start', 'payload':{}}))

        self.ltm_conn.close()

    def clear_stm(self):
        """
        """
        parser = argparse.ArgumentParser(
            description="sends a clear.all to stm exchange")
        self.ltm_chan.basic_publish(exchange='',
                                    routing_key='stm',
                                    body=json.dumps({'do':'clear_all', 'payload':{}}))
        self.ltm_conn.close()

    def build_api_for(self):
        parser = argparse.ArgumentParser(
            description="checks if the systems are up")

        parser.add_argument('mpid')
        arg = parser.parse_args(sys.argv[2:3])

        if len(arg.mpid) < self.max_arg_len:
            self.stm_chan.basic_publish(exchange='',
                                        routing_key='stm',
                                        body=json.dumps({'do':'build_api', 'payload':{"id": arg.mpid}}))

        self.stm_conn.close()

    def read_exchange(self):
        parser = argparse.ArgumentParser(
            description="read from exchange")

        self.stm_chan.basic_publish(exchange='',
                                    routing_key='stm',
                                    body=json.dumps({'do':'read_exchange', 'payload':{"id":"mpd-ce3-calib", "find_set":{"StartTime.Type":"start"}}}))

        self.stm_conn.close()

if __name__ == '__main__':
    Anselm()
