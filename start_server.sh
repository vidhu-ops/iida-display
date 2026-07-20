#!/bin/bash
exec gunicorn --config gunicorn_config.py --bind 0.0.0.0:5000 --reuse-port --reload main:app
