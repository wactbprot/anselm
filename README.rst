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

relayServer
===========

.. code-block:: shell
  
  curl -d '{"Action":"HTTP","Url":"http://localhost:50005/dut_max"}'  http://localhost:55555
  curl -d '{"Action":"HTTP","Url":"http://localhost:50005/target_pressures"}' http://localhost:55555
  curl -d '{"Action":"HTTP","Url":"http://localhost:50005/offset_sequences"}' http://localhost:55555
  