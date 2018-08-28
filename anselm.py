import sys
import json
import argparse
from threading import Thread
from anselm.system import System # pylint: disable=E0611
from anselm.long_term_memory import LongTermMemory # pylint: disable=E0611
from anselm.short_term_memory import ShortTermMemory # pylint: disable=E0611
from anselm.worker import Worker # pylint: disable=E0611

class Anselm(System):
    """
    https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html


    always talk to short-term-memory, if there is somthing not in stm try to remember
    """
    def __init__(self):
        super().__init__()
        
        self.ltm = LongTermMemory()
        self.stm = ShortTermMemory()
        self.worker = Worker()

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

    
    def clear_stm(self):
        self.stm.clear_stm()
    
    def build_auxobj_db_for(self):
        """
        usage:

        > python anselm provide_excahnge_for calid
        
        """
        parser = argparse.ArgumentParser(description="builds the api for the mp given by id")

        parser.add_argument('id')
        arg = parser.parse_args(sys.argv[2:3])

        if len(arg.id) < self.max_arg_len:
            doc = self.ltm.get_auxobj(arg.id)
            if doc:
                self.stm.build_auxobj_db(doc)

    def list_tasks_for(self):
        parser = argparse.ArgumentParser(description="list the tasks for given by id")

        parser.add_argument('id')

        arg = parser.parse_args(sys.argv[2:3])        
        id = arg.id
        if len(id) < self.max_arg_len:
             self.stm.get_tasknames(id)

    def run_task(self):
        parser = argparse.ArgumentParser(description="builds the api for the mp given by id")

        parser.add_argument('id')
        parser.add_argument('taskname')

        arg = parser.parse_args(sys.argv[2:4])        
        id = arg.id
        taskname = arg.taskname

        if len(id) < self.max_arg_len and len(taskname) < self.max_arg_len:
            task = self.stm.get_task(id, taskname)
            if task:
                Thread(target=self.worker.run, args=(task, )).start()
                self.log.info("start thread for task: {}".format(task['TaskName']))
            else:
                self.log.error("task not found")
        



   
if __name__ == '__main__':
    Anselm()
