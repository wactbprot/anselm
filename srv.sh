#!/bin/sh
export FLASK_APP=srv.py
export FLASK_DEBUG=1
export FLASK_ENV=development

flask run --host=0.0.0.0 --port=50005
