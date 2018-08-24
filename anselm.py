import sys
import json
import argparse
import pika
from anselm.system import System

class Anselm(System):
    """
    https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html


    always talk to short-term-memory, if there is somthing not in stm try to remember
    """
    def __init__(self):
        super().__init__()

        msg_dict = self.config['rabbitmq']
        host = msg_dict['host']
        self.msg_param = pika.ConnectionParameters(host=host)

        self.init_ctrl_msg_prod()
        self.init_stm_msg_prod()
        self.init_ltm_msg_prod()
        
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

    def ini_mps(self):
        """
        """       
        self.ltm_pub(body_dict={
                    'do':'get_mps',
                    'payload':{}
                    })
        self.ltm_conn.close()

    def clear_stm(self):
        """
        """
        
        self.stm_pub(body_dict={
                    'do':'clear_stm',
                    'payload':{}})
        self.stm_conn.close()

    

    def build_mp_db_for(self):
        """
        usage:

        > python anselm build_mp_db_for mpid

        """
        parser = argparse.ArgumentParser(
            description="builds the api for the mp given by id")

        parser.add_argument('mpid')
        arg = parser.parse_args(sys.argv[2:3])

        if len(arg.calid) < self.max_arg_len:
            self.ctrl_pub(body_dict={
                        'do':'build_mp_db',
                        'payload':{"id": arg.mpid}
                        })

        self.ctrl_conn.close()

    def build_cal_mp_for(self):
        """
        usage:

        > python anselm provide_excahnge_for calid
        
        """
        parser = argparse.ArgumentParser(
            description="builds the api for the mp given by id")

        parser.add_argument('calid')
        arg = parser.parse_args(sys.argv[2:3])

        if len(arg.calid) < self.max_arg_len:
            self.ctrl_pub(body_dict={
                        'do':'build_cal_db',
                        'payload':{"id": arg.calid}
                        })

        self.ctrl_conn.close()

    def read_exchange(self):
       
        self.stm_pub(body_dict={
                        'do':'read_exchange',
                        'payload':{"id":"mpd-ce3-calib", "find_set":{"StartTime.Type":"start"}}
                        })

        self.stm_conn.close()

if __name__ == '__main__':
    Anselm()
