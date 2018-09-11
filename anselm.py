import sys
import json

from anselm.system import System # pylint: disable=E0611
from anselm.db import DB # pylint: disable=E0611
from anselm.worker import Worker # pylint: disable=E0611
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication, QPushButton, QComboBox, QGridLayout, QPlainTextEdit
from PyQt5.QtCore import QThread, pyqtSignal , Qt
import sys


class Observe(QThread, System):
    signal = pyqtSignal('PyQt_PyObject')
    def __init__(self):
        QThread.__init__(self)
        System.__init__(self)
       
    def run(self):
        # git clone done, now inform the main thread with the output
    
        self.p.subscribe("io")
        print('Listening redis...')
        for item in self.p.listen():
            self.log.debug("received item: {}".format(item))
            if item['type'] == 'message':            
                self.signal.emit(int(item['data']))


class Anselm(System):
    fullscale = ["SRG", "0.1mbar", "0.25mbar","1mbar", 
                "10mbar", "100mbar", "1000mbar", "0.1Torr", 
                "1Torr", "10Torr", "100Torr", "1000Torr"]
    std_select = ["SE3", "CE3", "FRS5", "DKM_PPC4"]
    year_select = ["2017", "2018", "2019"]
    dut_branches = ["dut-a", "dut-b", "dut-c"]
    run_kinds = ["single", "loop"]

    def __init__(self):
        super().__init__()
       
        self.db = DB()
        self.worker = Worker()
        self.observer_thread = Observe()
        self.observer_thread.signal.connect(self.end_task)
        self.observer_thread.start()
        self.init_ui()
    
    def init_ui(self):
        self.current_grid_line = 1
        # head line
        self.add_device_btn_col = 1
        self.std_col = 2
        self.year_col = 3

        # device lines
        self.cal_id_col = 2
        self.fullscale_col = 3
        self.dut_branch_col = 4     
        self.auxobj_col = 5
        self.task_col = 6
        self.run_kind_col = 7
        self.run_btn_col = 8
        self.result_col= 1

        self.line_heigth = 28
        
        self.win = QWidget()
        self.grid = QGridLayout(self.win)

        add_device_bttn = QPushButton("add device", self.win)
        add_device_bttn.setFixedSize(450, self.line_heigth)
        add_device_bttn.clicked.connect(self.add_device_line)
        self.add_widget_to_grid(add_device_bttn ,self.current_grid_line, self.add_device_btn_col)
      
        std_select_combo = self.make_combo(self.std_select, first_item = None) 
       
        self.add_widget_to_grid(std_select_combo ,self.current_grid_line, self.std_col)
        std_select_combo.currentIndexChanged.connect(lambda: self.std_selected(std_select_combo))

        year_select_combo = self.make_combo(self.year_select, first_item = None) 
        self.add_widget_to_grid(year_select_combo ,self.current_grid_line, self.year_col)
        year_select_combo.currentIndexChanged.connect(lambda: self.year_selected(year_select_combo))

        self.draw_grid()  

    def add_widget_to_grid(self, widget, line, col):

        #old_widget_item = self.grid.itemAtPosition (line, col)
        #old_widget = old_widget_item.widget()
        
        self.grid.addWidget(widget, line, col)

    def make_combo(self, item_list, first_item='select'):
        c = QComboBox(self.win)
        if first_item:
            c.addItem(first_item)
        for item in item_list:
            c.addItem(item)
        return c

    def run_task(self, line):
        self.log.info("try to start device at line {}".format(line))
        self.worker.work_on_line = line
        self.worker.run()
    
    def end_task(self, line):
        self.add_widget_to_grid(self.make_result_label(line = line), line, self.result_col)

        self.log.info("end task at line {}".format(line))

    def add_device_line(self):
        self.current_grid_line +=1
        line = self.current_grid_line
        self.add_widget_to_grid(self.make_cal_id_combo(line = line), line, self.cal_id_col)
        self.add_widget_to_grid(self.make_auxobj_combo(line = line), line, self.auxobj_col)
        self.add_widget_to_grid(self.make_fullscale_combo(line = line), line, self.fullscale_col)
        self.add_widget_to_grid(self.make_dut_branch_combo(line = line), line, self.dut_branch_col)
        self.add_widget_to_grid(self.make_result_label(line = line), line, self.result_col)


    def draw_grid(self):
        self.win.setLayout(self.grid)
        self.win.setWindowTitle('Anselm')
        self.win.show()

    def make_run_bttn(self, line):
        b = QPushButton("run", self.win)  
        b.clicked.connect(lambda: self.run_task(line))

        return b

    def make_result_label(self, line):
        widget_item = self.grid.itemAtPosition (line, self.result_col)
        if widget_item:
            l = widget_item.widget()
        else:
            l = QPlainTextEdit(self.win)
            l.setFixedSize(450, self.line_heigth*2)
 
        result = self.aget('result', line)
        if result:
            txt = result
        else:
            txt = "raw output"

        l.setPlainText("{}".format(txt))
       
        return l

    def make_run_kind_combo(self, line):
       
        c = self.make_combo(self.run_kinds, first_item = None) 
        c.currentIndexChanged.connect(lambda: self.run_kind_selected(c, line))

        return c
   
    def make_dut_branch_combo(self, line):
       
        c = self.make_combo(self.dut_branches, first_item = "select branch") 
        c.currentIndexChanged.connect(lambda: self.dut_branch_selected(c, line))

        return c

    def make_fullscale_combo(self, line):
       
        c = self.make_combo(self.fullscale, first_item = "select device fullscale") 
        c.currentIndexChanged.connect(lambda: self.fullscale_selected(c, line))

        return c

    def make_cal_id_combo(self, line):
       
        cal_ids = self.db.get_cal_ids()
        c = self.make_combo(cal_ids, first_item = "select calib. document") 
        c.currentIndexChanged.connect(lambda: self.cal_id_selected(c, line))

        return c
   
    def make_auxobj_combo(self, line):
       
        aux_obj_ids = self.db.get_auxobj_ids()
       
        self.log.debug("found following auxobj ids {}".format(aux_obj_ids))
       
        c = self.make_combo(aux_obj_ids) 
        c.currentIndexChanged.connect(lambda: self.auxobj_selected(c, line))

        return c
    
    def make_task_combo(self, doc_id, line):
        task_names = self.db.get_task_names(doc_id = doc_id)
        self.log.debug("found following tasknames {}".format(task_names))
        c = self.make_combo(task_names) 
        c.currentIndexChanged.connect(lambda: self.task_selected(c, line))

        return c

    def run_kind_selected(self, combo, line):
        run_kind = combo.currentText()
        self.aset('run_kind', line, run_kind)

    def task_selected(self, combo, line):
        task_name = combo.currentText()
        doc_id = self.aget('doc_id', line)
        self.aset('task_name', line, task_name)
        task = self.db.get_task(doc_id, task_name)
        self.aset('task', line, task) 
        
        # add elements for next actions
        self.add_widget_to_grid(self.make_run_bttn(line=line), line, self.run_btn_col)
        self.add_widget_to_grid(self.make_run_kind_combo(line=line), line, self.run_kind_col)
 
        self.log.debug("task: {}".format(task))
        self.log.info("task with name {} selected at line {}".format(task_name, line))

    def auxobj_selected(self, combo, line):
        doc_id = combo.currentText()
        self.aset('doc_id', line, doc_id)
        self.log.debug("select {} at line {}".format(doc_id, line))
        task_combo = self.make_task_combo(doc_id = doc_id, line = line)
        self.add_widget_to_grid(widget=task_combo, line=line, col=self.task_col)
        #self.draw_grid()
    
    def cal_id_selected(self, combo, line):
        cal_id = combo.currentText()
        self.aset('calid', line, cal_id)
        self.log.info("select calibration id {}".format( cal_id )) 

    def fullscale_selected(self, combo, line):
        fs = combo.currentText()
        self.aset('fullscale', line, fs)
        self.log.info("select fullscale {}".format( fs ))

    def dut_branch_selected(self, combo, line):
        dut = combo.currentText()
        self.aset('dut_branch', line, dut)
        self.log.info("device at line {} attached to {}".format(line,  dut ))

    def std_selected(self, combo):
        standard = combo.currentText()
        self.aset('standard', 0,  standard )
        self.log.info("select standard {}".format( standard))
    
    def year_selected(self, combo):
        year = combo.currentText()
        self.aset('year', 0, year)
        self.log.info("select year {}".format( year ))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Anselm()
    sys.exit(app.exec_())
