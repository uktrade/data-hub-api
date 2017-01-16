#!/bin/bash -xe
python /app/manage.py migrate
python /app/manage.py collectstatic --noinput
gunicorn config.wsgi --bind=0.0.0.0:8000
