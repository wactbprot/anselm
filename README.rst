anselm
======



requirements
============

* couchdb (long-term memory, ltm)
* mongodb (short-term memory, stm)
* rabbidmq (message broker, msg)

todo rabbitmq
=============
* proper shutdown

todo config
===========

* config.json entries for exchanges and queues together with
  description of their functionality


build api
=========

Idea is:
* make exchange, container etc. databases
* collections with mp_def id

exchange and insert_one
=======================
How to organize a fast write_to_exchange?

Idea is:
Don't search and replace if an entry already exist.
Use ``insert_one`` regardless of already existing documents. Simply
read out the last written document by ``db.coll.find().limit(1)``.
But:
This may become slow if N goes up (e.g. on setting pressure 
processes N will be several 1000)
