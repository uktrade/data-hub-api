#!/bin/bash -xe
python /app/leeloo/manage.py migrate
python /app/leeloo/manage.py collectstatic --noinput
gunicorn datahubapi.wsgi --bind=0.0.0.0:8000
