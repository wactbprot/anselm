anselm
======

requirements
============

* couchdb 
* redis
* PyQt5
* flask

redis
=====

install on opensuse with (su):

.. code-block:: shell

    > zypper ref
    > zypper in redis
    > cp -a /etc/redis/default.conf.example /etc/redis/default.conf
    > chown root:redis  /etc/redis/default.conf
    > chmod u=rw,g=r,o= /etc/redis/default.conf
    > 
    > install -d -o redis -g redis -m 0750 /var/lib/redis/default/
    > 
    > systemctl start redis@default
    > systemctl enable redis@default


install and run
===============

.. code-block:: shell

    > python3 -m venv /path/to/anselm
    > cd /path/to/anselm
    > source bin/activate
    > pip install -e .
    > 
    > ./anselm.sh & ./srv.sh


CustomerObject example
======================

.. code-block:: json
  
  {
  "_id": "cuob-ctrl-cdg_mks670_gpib",
  
  "CustomerObject": {
    "Type": "CDG Controler MKS 670",
    "Name": "MKS_CDG670_GPIB",
    "Owner": {
      "Name": "PTB AG7.54"
    },
    "Device": {
      "Producer": "MKS"
    },
    "Date": {
      "Type": "generated",
      "Value": "2018-09-17"
    },
    "Defaults": {
      "@host": "e75416",
      "@device": "gpib0,13",
      "@unit": "mbar",
      "@acc": "VXI11"
    },
    "Task": [
      {
        "TaskName": "auto_init_low_range",
        "Comment": "Task initializes the X0.01 range",
        "Action": "@acc",
        "Host": "@host",
        "VxiTimeout": 0,
        "Device": "@device",
        "From": "@fullscale/10000",
        "To": "@fullscale/100",
        "Value": ":sens:scan(@1):gain X0.01",
        "PostProcessing": [
          "ToExchange={'@exchpath':_x == null};"
        ]
      },
      {
        "TaskName": "auto_init_med_range",
        "Comment": "Task initializes the X0.01 range",
        "Action": "@acc",
        "VxiTimeout": 0,
        "Host": "@host",
        "Device": "@device",
        "From": "@fullscale/100",
        "To": "@fullscale/10",
        "Value": ":sens:scan(@1):gain X0.1",
        "PostProcessing": [
          "ToExchange={'@exchpath':_x == null};"
        ]
      },
      {
        "TaskName": "auto_init_high_range",
        "Comment": "Task initializes the X0.01 range",
        "Action": "@acc",
        "VxiTimeout": 0,
        "Host": "@host",
        "Device": "@device",
        "From": "@fullscale/10",
        "To": "@fullscale",
        "Value": ":sens:scan(@1):gain X1",
        "PostProcessing": [
          "ToExchange={'@exchpath':_x == null};"
        ]
      },
      {
        "TaskName": "auto_offset_low_range",
        "Comment": "Saves an offset sample in AuxValues",
        "Action": "@acc",
        "VxiTimeout": 0,
        "Host": "@host",
        "Device": "@device",
        "DocPath": "Calibration.Measurement.AuxValues.Pressure",
        "Value": ":meas:func",
        "Repeat": "100",
        "Wait": "1000",
        "PostProcessing": [
          "var _vec=_x.map(_.extractMKSCDG).map(parseFloat),",
          "Result=[_.vlRes('offset_x0.01',_vec,'@unit')];"
        ]
      },
      {
        "TaskName": "auto_offset_med_range",
        "Comment": "Saves an offset sample in AuxValues",
        "Action": "@acc",
        "VxiTimeout": 0,
        "Host": "@host",
        "Device": "@device",
        "DocPath": "Calibration.Measurement.AuxValues.Pressure",
        "Value": ":meas:func",
        "Repeat": "100",
        "Wait": "1000",
        "PostProcessing": [
          "var _vec=_x.map(_.extractMKSCDG).map(parseFloat),",
          "Result=[_.vlRes('offset_x0.1',_vec,'@unit')];"
        ]
      },
      {
        "TaskName": "auto_offset_high_range",
        "Comment": "Saves an offset sample in AuxValues",
        "Action": "@acc",
        "VxiTimeout": 0,
        "Host": "@host",
        "Device": "@device",
        "DocPath": "Calibration.Measurement.AuxValues.Pressure",
        "Value": ":meas:func",
        "Repeat": "100",
        "Wait": "1000",
        "PostProcessing": [
          "var _vec=_x.map(_.extractMKSCDG).map(parseFloat),",
          "Result=[_.vlRes('offset_x1',_vec,'@unit')];"
        ]
      },
      {
        "TaskName": "offset",
        "Action": "@acc",
        "VxiTimeout": 0,
        "Host": "@host",
        "Device": "@device",
        "LogPriority": "3",
        "DocPath": "Calibration.Mesaurement.Values.Pressure",
        "Value": ":meas:func",
        "Repeat": "15",
        "Wait": "1000",
        "PostProcessing": [
          "var _last = _x.length - 1;",
          "_x = _x.slice(4,_last);",
          "_t_start = _t_start.slice(4,_last);",
          "_t_stop = _t_stop.slice(4,_last);",
          "var _vec=_x.map(_.extractMKSCDG).map(parseFloat),",
          "_res = _.vlStat(_.checkNumArr(_vec).Arr),",
          "Result=[_.vlRes('ind_offset',_res.mv,'@unit', '',_res.sd, _res.N)];"
        ]
      },
      {
        "TaskName": "ind",
        "Action": "@acc",
        "VxiTimeout": 0,
        "Host": "@host",
        "Device": "@device",
        "LogPriority": "3",
        "DocPath": "Calibration.Mesaurement.Values.Pressure",
        "Value": ":meas:func",
        "Repeat": "15",
        "Wait": "1000",
        "PostProcessing": [
          "var _last = _x.length - 1;",
          "_x = _x.slice(4,_last);",
          "_t_start = _t_start.slice(4,_last);",
          "_t_stop = _t_stop.slice(4,_last);",
          "var _vec=_x.map(_.extractMKSCDG).map(parseFloat),",
          "_res = _.vlStat(_.checkNumArr(_vec).Arr),",
          "Result=[_.vlRes('ind',_res.mv,'@unit', '',_res.sd, _res.N)];"
        ]
      }
    ]
  }
  }

