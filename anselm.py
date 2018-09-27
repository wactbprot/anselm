import sys
import json

from anselm.system import System # pylint: disable=E0611
from anselm.db import DB # pylint: disable=E0611
from anselm.worker import Worker # pylint: disable=E0611
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication, QPushButton
from PyQt5.QtWidgets import QComboBox, QGridLayout, QPlainTextEdit, QLabel, QLineEdit
from PyQt5.QtCore import QThread, pyqtSignal , Qt


class Observe(QThread, System):
    signal = pyqtSignal('PyQt_PyObject')
    def __init__(self):
        QThread.__init__(self)
        System.__init__(self)

    def run(self):
        self.p.subscribe("io")
        self.log.info('start listening redis ')
        for item in self.p.listen():
            self.log.debug("received item: {}".format(item))
            if item['type'] == 'message':
                self.signal.emit(int(item['data']))


class Anselm(System):
    
    std_select = ["SE3", "CE3", "FRS5", "DKM_PPC4"]
    year_select = ["2019", "2018", "2017"]
    dut_branches = ["dut_a", "dut_b", "dut_c"]
   
    mult_line_height = 4
    current_grid_line = 1

    std_col = 1
    year_col = 2
    add_device_btn_col = 3
    
    std_line = 1
    year_line = 1
    add_device_btn_line = 1

    cal_id_col = 2
    fullscale_col = 3
    dut_branch_col = 4
    devices_col = 5
    task_col = 6
    run_btn_col = 7
    result_col= 1
   
    start_defaults_col = 8
    line_heigth = 28
    long_line = 200
    med_line = 80

    def __init__(self):
        super().__init__()
        self.fullscale_list = [
                                {"Unit":self.unit, "Display":"SRG"     , "Value":2.0},  
                                {"Unit":self.unit, "Display":"0.1mbar" , "Value":10.0},  
                                {"Unit":self.unit, "Display":"0.25mbar", "Value":25.0}, 
                                {"Unit":self.unit, "Display":"1mbar"   , "Value":100}, 
                                {"Unit":self.unit, "Display":"10mbar"  , "Value":1000.0},  
                                {"Unit":self.unit, "Display":"100mbar" , "Value":10000.},  
                                {"Unit":self.unit, "Display":"1000mbar", "Value":100000.0},  
                                {"Unit":self.unit, "Display":"0.1Torr" , "Value":13.3}, 
                                {"Unit":self.unit, "Display":"1Torr"   , "Value":133.0},  
                                {"Unit":self.unit, "Display":"10Torr"  , "Value":1330.0},  
                                {"Unit":self.unit, "Display":"100Torr" , "Value":13300.0},  
                                {"Unit":self.unit, "Display":"1000Torr", "Value":133000.0}, 
                                ]
        self.range_exprs = {
                            "fullscale" :1,
                            "fullscale/10" :0.1,
                            "fullscale/100" :0.01,
                            "fullscale/10000" :0.0001,
                            "fullscale/100000" :0.00001,
                        }

        self.db = DB()
        self.worker = Worker()
        self.observer_thread = Observe()
        self.observer_thread.signal.connect(self.end_task)
        self.observer_thread.start()
        self.init_ui()

    def init_ui(self):

        self.win = QWidget()
        self.win.closeEvent = self.closeEvent
        self.grid = QGridLayout(self.win)

        self.add_widget_to_grid(self.make_std_combo(),self.std_line, self.std_col)
        self.draw_grid()

    def make_label_edit_pair(self, label_val, edit_val, line):

        label_widget = QLabel(str(label_val), self.win)
        edit_widget = QLineEdit(str(edit_val),  self.win)
        edit_widget.setFixedSize(self.med_line, self.line_heigth)
        edit_widget.textChanged[str].connect(lambda: self.default_change(edit_widget, str(label_val), line))
        
        return label_widget, edit_widget

    def make_add_device_button(self):

        b = QPushButton("add device line", self.win)
        b.setStyleSheet("background-color: yellow")
        b.clicked.connect(self.add_device_line)

        return b

    def make_std_combo(self):
        c = self.make_combo(self.std_select, first_item="select primary standard", last_item=False)
        c.setFixedSize(self.long_line, self.line_heigth)
        c.currentIndexChanged.connect(lambda: self.std_selected(c))

        return c

    def make_year_combo(self):
        c = self.make_combo(self.year_select, first_item="select calibration year", last_item=False)
        c.currentIndexChanged.connect(lambda: self.year_selected(c))

        return c

    def add_widget_to_grid(self, widget, line, col):

        #old_widget_item = self.grid.itemAtPosition (line, col)
        #old_widget = old_widget_item.widget()

        self.grid.addWidget(widget, line, col)

    def make_combo(self, item_list, first_item=True, last_item=True):
        c = QComboBox(self.win)

        if first_item:
            if isinstance(first_item, bool):
                c.addItem(self.first_item)
            if isinstance(first_item, str):
                c.addItem(first_item)

        for item in item_list:
            c.addItem(item)

        if last_item:
            if isinstance(last_item, bool):
                c.addItem(self.last_item)
            if isinstance(last_item, str):
                c.addItem(last_item)

        return c

    def run_task(self, line):
        self.log.info("try to start device at line {}".format(line))
        self.worker.work_on_line = line
        self.worker.run()

    def end_task(self, line):
        self.add_widget_to_grid(self.make_result_label(line = line), line, self.result_col)
        self.db.save_results()
        self.log.info("end task at line {}".format(line))

    def add_device_line(self):
        self.current_grid_line +=1
        
        line = self.current_grid_line
        self.add_widget_to_grid(self.make_cal_id_combo(line = line), line, self.cal_id_col)
        self.add_widget_to_grid(self.make_device_combo(line = line), line, self.devices_col)
        self.add_widget_to_grid(self.make_fullscale_combo(line = line), line, self.fullscale_col)
        self.add_widget_to_grid(self.make_dut_branch_combo(line = line), line, self.dut_branch_col)
        self.add_widget_to_grid(self.make_result_label(line = line), line, self.result_col)

    def draw_grid(self):
        self.win.setLayout(self.grid)
        self.win.setWindowTitle('Anselm')
        self.win.show()

    def make_result_label(self, line):
        widget_item = self.grid.itemAtPosition (line, self.result_col)
        if widget_item:
            l = widget_item.widget()
        else:
            l = QPlainTextEdit(self.win)
            l.setFixedSize(self.long_line, self.line_heigth*self.mult_line_height)
        l.setStyleSheet("background-color: lightyellow")
        result = self.aget('result', line)
        exchange = self.aget('exchange', line)
        if result:
            txt = str(result)
        elif exchange:
            txt = str(exchange)
        else:
            txt = ""
        
        txt = txt.replace(",", ",\n")

        l.setPlainText("{}".format(txt))

        return l
    
    def make_run_button(self, line):

        b = QPushButton("test selected task", self.win)
        b.setStyleSheet("background-color: lightgreen")
        b.clicked.connect(lambda: self.run_selected(b, line))

        return b

    def make_dut_branch_combo(self, line):

        c = self.make_combo(self.dut_branches, first_item="select branch")
        c.currentIndexChanged.connect(lambda: self.dut_branch_selected(c, line))

        return c

    def make_fullscale_combo(self, line):
        fullscale = []
        for d  in self.fullscale_list:
            fullscale.append(d['Display'])

        c = self.make_combo(fullscale, first_item="select fullscale")
        c.currentIndexChanged.connect(lambda: self.fullscale_selected(c, line))

        return c

    def make_cal_id_combo(self, line):

        cal_ids = self.db.get_cal_ids()
        c = self.make_combo(cal_ids, first_item="select calibration")
        c.currentIndexChanged.connect(lambda: self.cal_id_selected(c, line))

        return c

    def make_device_combo(self, line):

        device_ids = self.db.get_device_ids()

        self.log.debug("found following devices ids {}".format(device_ids))

        c = self.make_combo(device_ids, first_item="select read out device", last_item=False)
        c.currentIndexChanged.connect(lambda: self.device_selected(c, line))

        return c

    def make_task_combo(self, doc_id, line):
        ok = False
        tasks = self.db.get_tasks(doc_id = doc_id)
        if tasks:
            self.log.debug("found {} tasks ".format(len(tasks)))
            ok = self.evaluate_auto_tasks(tasks, line)
        
            if ok:
                first_item = "tasks ok"
                c = self.make_combo([task.get('TaskName') for task in tasks], first_item=first_item, last_item=False)
                c.currentIndexChanged.connect(lambda: self.task_selected(c, line))
            else:
                first_item = "task name problem"
                c = self.make_combo([task.get('TaskName') for task in tasks], first_item=first_item, last_item=False)
        else:
            first_item = "no task"
            c = self.make_combo([], first_item=first_item, last_item=False)
            
        return c

    def get_pressure_from_range_expr(self, range_expr, line):
        value = self.fget("fullscale_value", line)
        unit = self.aget("fullscale_unit", line)

        if unit and value and range_expr in  self.range_exprs:
            value =  value * self.range_exprs[range_expr]
           
            self.log.debug("found {} {}".format(value, unit))
            
            return value, unit

        else:
            msg = "unknown range expression"
            self.log.error(msg)
            return None, None

    def evaluate_auto_tasks(self, tasks, line):
        offset_all_sequence = []
        auto_init_tasks = []
        auto_offset_tasks = []

        res = True
        for task in tasks:
            task_name = task.get('TaskName')
            if 'From' in task:
                task['From'] , task['FromUnit'] , = self.get_pressure_from_range_expr(task.get('From'), line)
            if 'To' in task:
                task['To'] , task['ToUnit'] , = self.get_pressure_from_range_expr(task.get('To'), line)
                    
            if task_name.startswith('auto_init_'):
                auto_init_tasks.append(task)

            if  task_name.startswith('auto_offset_'):        
                auto_offset_tasks.append(task)
           
            if task_name == 'offset':
                self.aset('offset_task', line, task)
           
            if task_name == 'ind':
                self.aset('ind_task', line, task)
        
        for init_task in auto_init_tasks:
            sufix = init_task.get('TaskName').replace("auto_init_", "")
            related_offset_task =  "auto_offset_{}".format(sufix)
            for offset_task in  auto_offset_tasks:
                if offset_task.get('TaskName') ==  related_offset_task:
                    offset_all_sequence.append(init_task) 
                    offset_all_sequence.append(offset_task)

       
        self.aset("offset_all_sequence", line, offset_all_sequence)
        self.aset("auto_init_tasks", line, auto_init_tasks)
        return res

    def run_selected(self, combo, line):
        self.aset('save', 0,  "no" )
        self.log.info("set save to [no]")
        self.run_task(line)
    
    def task_selected(self, combo, line):

        task_name = combo.currentText()
        
        self.db.choose_task(task_name, line)

        # add elements for next actions
        self.add_widget_to_grid(self.make_run_button(line=line), line, self.run_btn_col)

        self.log.info("task with name {} selected at line {}".format(task_name, line))

    def device_selected(self, combo, line):

        doc_id = combo.currentText()
        self.aset('doc_id', line, doc_id)
        self.log.debug("select {} at line {}".format(doc_id, line))
        task_combo = self.make_task_combo(doc_id = doc_id, line = line)
        if task_combo:
            self.add_widget_to_grid(widget=task_combo, line=line, col=self.task_col)
            defaults = self.db.get_defaults(doc_id)
            self.aset('defaults', line, defaults)

            current_defaults_col = self.start_defaults_col
            for label_val, edit_val in defaults.items():
                self.log.debug(label_val)
                self.log.debug(edit_val)
                label_widget, edit_widget = self.make_label_edit_pair(label_val, edit_val, line)
                self.add_widget_to_grid(label_widget, line, current_defaults_col)
                self.add_widget_to_grid(edit_widget, line, current_defaults_col +1)
                current_defaults_col = current_defaults_col +2
        
    def cal_id_selected(self, combo, line):
        cal_id = combo.currentText()
        self.aset('cal_id', line, cal_id)
        self.log.info("select calibration id {}".format( cal_id ))

    def fullscale_selected(self, combo, line):
        fs = combo.currentText()
        for d in self.fullscale_list:
            if d.get('Display') == fs:
                self.aset('fullscale_display', line, d['Display'])
                self.aset('fullscale_value', line, d['Value'])
                self.aset('fullscale_unit', line, d['Unit'])

                self.log.info("select fullscale {}".format( fs ))
                break

    def dut_branch_selected(self, combo, line):
        dut = combo.currentText()
        self.aset('dut_branch', line, dut)
        self.log.info("device at line {} attached to {}".format(line,  dut ))

    def std_selected(self, combo):
        standard = combo.currentText()
        self.aset('standard', 0,  standard )
        self.add_widget_to_grid(self.make_year_combo() ,self.year_line, self.year_col)
        self.log.info("select standard {}".format( standard))
    
    def year_selected(self, combo):
        year = combo.currentText()
        self.aset('year', 0, year)
        self.log.info("select year {}".format( year ))
        self.add_widget_to_grid(self.make_add_device_button(), self.add_device_btn_line, self.add_device_btn_col) 
        
    def default_change(self, edit_widget, label_val, line):
        self.log.debug(label_val)
        defaults = self.dget('defaults', line)
        task_db = self.dget('task_db', line)

        if label_val in defaults:
            defaults[label_val] = str(edit_widget.text())
            self.aset('defaults', line, defaults)
            task = self.db.replace_defaults(task=task_db, defaults=defaults)
            self.aset('task', line, task)

    def closeEvent(self, event):
        self.log.info("flush redis database, bye!")
        self.r.flushdb()
        if True:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    Anselm()
    sys.exit(app.exec_())
