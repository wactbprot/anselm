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
    year_select = ["2019", "2018", "2017"]
    dut_branches = ["dut-a", "dut-b", "dut-c"]
    run_kinds = ["single", "loop"]
  
    mult_line_height = 4
    current_grid_line = 1

    add_device_btn_col = 3
    std_col = 1
    year_col = 2

    cal_id_col = 2
    fullscale_col = 3
    dut_branch_col = 4
    auxobj_col = 5
    task_col = 6
    run_kind_col = 7
    run_btn_col = 8
    result_col= 1
    line_heigth = 28
    long_line = 200

    def __init__(self):
        super().__init__()

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

        self.add_widget_to_grid(self.make_std_combo(),self.current_grid_line, self.std_col)
        self.draw_grid()

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

    def make_result_label(self, line):
        widget_item = self.grid.itemAtPosition (line, self.result_col)
        if widget_item:
            l = widget_item.widget()
        else:
            l = QPlainTextEdit(self.win)
            l.setFixedSize(self.long_line, self.line_heigth*self.mult_line_height)
        l.setStyleSheet("background-color: lightyellow")
        result = self.aget('result', line)
        if result:
            txt = str(result)
            txt = txt.replace(",", ",\n")
        else:
            txt = ""

        l.setPlainText("{}".format(txt))

        return l

    def make_run_kind_combo(self, line):

        c = self.make_combo(self.run_kinds, first_item="run:", last_item=False)
        c.currentIndexChanged.connect(lambda: self.run_kind_selected(c, line))

        return c

    def make_dut_branch_combo(self, line):

        c = self.make_combo(self.dut_branches, first_item="select branch")
        c.currentIndexChanged.connect(lambda: self.dut_branch_selected(c, line))

        return c

    def make_fullscale_combo(self, line):

        c = self.make_combo(self.fullscale, first_item="select fullscale")
        c.currentIndexChanged.connect(lambda: self.fullscale_selected(c, line))

        return c

    def make_cal_id_combo(self, line):

        cal_ids = self.db.get_cal_ids()
        c = self.make_combo(cal_ids, first_item="select calibration")
        c.currentIndexChanged.connect(lambda: self.cal_id_selected(c, line))

        return c

    def make_auxobj_combo(self, line):

        aux_obj_ids = self.db.get_auxobj_ids()

        self.log.debug("found following auxobj ids {}".format(aux_obj_ids))

        c = self.make_combo(aux_obj_ids, first_item="select read out device", last_item=False)
        c.currentIndexChanged.connect(lambda: self.auxobj_selected(c, line))

        return c

    def make_task_combo(self, doc_id, line):
        task_names = self.db.get_task_names(doc_id = doc_id)
        self.log.debug("found following tasknames {}".format(task_names))
        c = self.make_combo(task_names, first_item="select task", last_item=False)
        c.currentIndexChanged.connect(lambda: self.task_selected(c, line))

        return c

    def run_kind_selected(self, combo, line):
        run_kind = combo.currentText()
        self.aset('run_kind', line, run_kind)
        self.run_task(line)

    def task_selected(self, combo, line):
        task_name = combo.currentText()
        doc_id = self.aget('doc_id', line)
        self.aset('task_name', line, task_name)
        task = self.db.get_task(doc_id, task_name)
        self.aset('task', line, task)

        # add elements for next actions
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
        self.add_widget_to_grid(self.make_year_combo() ,self.current_grid_line, self.year_col)
        self.log.info("select standard {}".format( standard))

    def year_selected(self, combo):
        year = combo.currentText()
        self.aset('year', 0, year)
        self.add_widget_to_grid(self.make_add_device_button(), self.current_grid_line, self.add_device_btn_col) 
        self.log.info("select year {}".format( year ))

    def closeEvent(self, event):
        self.log.info("flush redis database")
        self.r.flushdb()
        if True:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    Anselm()
    sys.exit(app.exec_())
