import sys
import json
import argparse
from threading import Thread
from anselm.system import System # pylint: disable=E0611
from anselm.db import DB # pylint: disable=E0611
from anselm.worker import Worker # pylint: disable=E0611
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication, QPushButton, QComboBox, QGridLayout, QLineEdit

import sys


class Anselm(System):
   

    def __init__(self):
        super().__init__()
              
        self.db = DB()
        self.worker = Worker()
        self.current_grid_line = 1
        self.initUI()
       
    def initUI(self):
        self.win = QWidget()
        self.win.resize(250, 150)
        self.win.setWindowTitle('Anselm')
        self.grid = QGridLayout()

        add_device_bttn = QPushButton("add device", self.win)
        add_device_bttn.clicked.connect(self.add_device_line)
      
        std_select = ["SE3", "CE3", "FRS5", "DKM_PPC4"]
        std_select_combo = self.make_combo(std_select, first_item = None) 

        self.add_widget_to_grid(std_select_combo ,1, 1)
        self.add_widget_to_grid(add_device_bttn ,1, 2)
        std_select_combo.currentIndexChanged.connect(lambda: self.std_selected(std_select_combo))
        self.draw_grid()        
        
    def add_device_line(self):
        self.current_grid_line +=1
        line = self.current_grid_line
        line_key = self.get_line_key(line)

        self.state[line_key] = {}
        
        run_bttn = self.make_run_bttn(line = line)
        auxobj_combo = self.make_auxobj_combo(line = line)
        run_kind_combo = self.make_run_kind_combo(line = line)

        self.add_widget_to_grid(run_bttn, line, 1)
        self.add_widget_to_grid(run_kind_combo, line, 2)
        self.add_widget_to_grid(auxobj_combo, line, 3)
        self.draw_grid()

    def draw_grid(self):
        self.win.setLayout(self.grid)
        self.win.show()

    def make_run_bttn(self, line):
        run_device_bttn = QPushButton("run", self.win)  
        run_device_bttn.clicked.connect(lambda: self.run_device(line))

        return run_device_bttn

    def make_result_textbox(self, line):
        result_textbox = QLineEdit(self.win)
        result_textbox.resize(280,40)

        return result_textbox

    def make_run_kind_combo(self, line):
       
        run_kinds = ["single", "loop"]
        combo = self.make_combo(run_kinds, first_item = None) 
        combo.currentIndexChanged.connect(lambda: self.run_kind_selected(combo, line))

        return combo
   
    def make_calib_id_combo(self, line):
       
        run_kinds = ["single", "loop"]
        combo = self.make_combo(run_kinds, first_item = None) 
        combo.currentIndexChanged.connect(lambda: self.run_kind_selected(combo, line))

        return combo
   
    def make_auxobj_combo(self, line):
       
        aux_obj_ids = self.db.get_auxobj_ids()
       
        self.log.debug("found following auxobj ids {}".format(aux_obj_ids))
       
        combo = self.make_combo(aux_obj_ids) 
        combo.currentIndexChanged.connect(lambda: self.auxobj_selected(combo, line))

        return combo
    
    def make_task_combo(self, doc_id, line):
       
        task_names = self.db.get_task_names(doc_id = doc_id)
       
        self.log.debug("found following tasknames {}".format(task_names))
       
        combo = self.make_combo(task_names) 
        combo.currentIndexChanged.connect(lambda: self.task_selected(combo, line))

        return combo

    def run_kind_selected(self, combo, line):

        run_kind = combo.currentText()
        line_key = self.get_line_key(line)
        self.state[line_key]['run_kind'] = run_kind

    def task_selected(self, combo, line):

        line_key = self.get_line_key(line)

        doc_id = self.state.get(line_key).get('doc_id')
        task_name = combo.currentText()
        self.state[line_key]['task_name'] = task_name

        self.log.info("task with name {} selected at line {}".format(task_name, line))
        self.log.debug("state dict: {}".format(self.state))
        
        task = self.db.get_task(doc_id, task_name)
        self.state[line_key]['task'] = task 
        self.log.debug("task: {}".format(task))

        self.make_result_textbox(line)

    def auxobj_selected(self, combo, line):
        doc_id = combo.currentText()
        line_key = self.get_line_key(line)

        self.state[line_key]['doc_id'] = doc_id 

        self.log.debug("select {} at line {}".format(doc_id, line))

        auxobj_combo = self.make_task_combo(doc_id = doc_id, line = line)
        self.add_widget_to_grid(widget=auxobj_combo, line=line, col=4)
        self.draw_grid()

    def add_widget_to_grid(self, widget, line, col):

        #old_widget_item = self.grid.itemAtPosition (line, col)
        #old_widget = old_widget_item.widget()
        
        self.grid.addWidget(widget, line, col)

    def make_combo(self, item_list, first_item='select'):
        combo = QComboBox(self.win)

        if first_item:
            combo.addItem(first_item)

        for item in item_list:
            combo.addItem(item)
        return combo

    def get_line_key(self, line):
        return 'line_{}'.format(line)

    def run_device(self, line):
        line_key = self.get_line_key(line)
        task = None

        self.log.info("start device at line {}".format(line))
        if line_key in self.state:
            if 'task' in self.state[line_key]:
                task = self.state[line_key]['task']  
            else:
                self.log.error("no task selected at line {}".format(line))
        if task:
            self.log.debug("task is: {}".format(task))
            Thread(target=self.worker.run, args=(task, )).start()
       
    def std_selected(self, combo):
        self.state['standard'] = combo.currentText()
        self.log.info("select standard {}".format( self.state.get('standard')))

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Anselm()
    sys.exit(app.exec_())

