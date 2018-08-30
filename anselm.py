import sys
import json
import argparse
from threading import Thread
from anselm.system import System # pylint: disable=E0611
from anselm.db import DB # pylint: disable=E0611
from anselm.worker import Worker # pylint: disable=E0611
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication, QPushButton, QComboBox, QGridLayout

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

        self.win.add_device_bttn = QPushButton("add device", self.win)
        self.win.add_device_bttn.clicked.connect(self.add_device_line)
      
        self.grid.addWidget( self.win.add_device_bttn ,self.current_grid_line, 1)

        self.draw_grid()        
        
    def add_device_line(self):
        self.current_grid_line +=1
       
        self.grid.addWidget(self.make_run_bttn(line = self.current_grid_line), self.current_grid_line,1)
        self.grid.addWidget(self.make_auxobj_combo(line = self.current_grid_line), self.current_grid_line,2)
             
        self.draw_grid()

    def draw_grid(self):
        self.win.setLayout(self.grid)
        self.win.show()

    def make_run_bttn(self, line):
        run_device_bttn = QPushButton("run", self.win)  
        run_device_bttn.clicked.connect(lambda: self.run_device(line))

        return run_device_bttn

    def make_auxobj_combo(self, line):
       
        aux_obj_ids = self.db.get_auxobj_ids()
       
        self.log.debug("found following auxobj ids {}".format(aux_obj_ids))
       
        combo = self.make_combo(aux_obj_ids) 
        combo.currentIndexChanged.connect(lambda: self.auxobj_selected(combo, line))

        return combo

    def make_task_combo(self, line):
       
        aux_obj_ids = self.db.get_auxobj_ids()
       
        self.log.debug("found following auxobj ids {}".format(aux_obj_ids))
       
        combo = self.make_combo(aux_obj_ids) 
        combo.currentIndexChanged.connect(lambda: self.auxobj_selected(combo, line))

        return combo


    def auxobj_selected(self, combo, line):
        self.log.debug("select {} at line {}".format(combo.currentText(), line))
        self.grid.addWidget(self.make_auxobj_combo(line = self.current_grid_line), line, 3)
             
        self.draw_grid()



    def make_combo(self, item_list):
        combo = QComboBox(self.win)
        combo.addItem("select")

        for item in item_list:
            combo.addItem(item)
        return combo

    def run_device(self, line):
        self.log.info("start device at line {}".format(line))

    def run_task(self, task):
        if task:
            Thread(target=self.worker.run, args=(task, )).start()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Anselm()
    sys.exit(app.exec_())

