import sys
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

        parser = argparse.ArgumentParser(
            description='check systems',
            usage='''anselm <command> [<args>]''')

        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command):
            parser.print_help()
            exit(1)

        getattr(self, args.command)()

    def init_ltm_msg_prod(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.exchange_declare(exchange='ltm',
                            exchange_type='topic')
        self.ltm_conn = conn
        self.ltm_chan = chan

    def init_stm_msg_prod(self):
        conn = pika.BlockingConnection(self.msg_param)
        chan = conn.channel()
        chan.exchange_declare(exchange='stm',
                            exchange_type='topic')
        self.ltm_conn = conn
        self.ltm_chan = chan

    def to_ltm(self):
        parser = argparse.ArgumentParser(
            description="checks if the systems are up")

        self.ltm_chan.basic_publish(exchange='ltm',
                                    routing_key='ltm.all',
                                    body='')

        self.ltm_conn.close()


if __name__ == '__main__':
    Anselm()
