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


install 
=======

.. code-block:: shell

    > python3 -m venv /path/to/anselm
    > cd /path/to/anselm
    > source bin/activate
    > pip install -e .
    > 
    > ./anselm.sh & ./srv.sh

check systems
=============

.. code-block:: shell

    > python3 -m venv /path/to/anselm
    > cd /path/to/anselm
    > source bin/activate
    > 
    > python  se3_system_check.py

should start with:

.. code-block:: shell

        root[30431] INFO **************check redis connection**************
        root[30431] INFO redis [ok]
        root[30431] INFO ****************check relayServer*****************
        root[30431] INFO relayServer [ok]
        root[30431] INFO ******************check database******************
        root[30431] INFO database [ok]
        root[30431] INFO *****************check valves mpd*****************
        root[30431] INFO valves mp [ok]
        root[30431] INFO *****************check servo mpd******************
        root[30431] INFO servo mp [ok]


run
===

.. code-block:: shell

    > python3 -m venv /path/to/anselm
    > cd /path/to/anselm
    > source bin/activate
    > pip install -e .
    > 
    > ./anselm.sh & ./srv.sh

curl
====

.. code-block:: shell
  
  curl http://localhost:50005/dut_max
  curl http://localhost:50005/target_pressures
  curl http://localhost:50005/offset_sequences

  curl -H "Content-Type: application/json" -d '{"Target_pressure_value":"1","Target_pressure_unit":"Pa"}'  -X 'POST' http://localhost:50005/offset
  curl -H "Content-Type: application/json" -d '{"Target_pressure_value":"1","Target_pressure_unit":"Pa"}'  -X 'POST' http://localhost:50005/ind
  curl -H "Content-Type: application/json" -d '{"DocPath":"Calibration.Measurement.AuxValues.Branch"}'  -X 'POST' http://localhost:50005/save_dut
  
 