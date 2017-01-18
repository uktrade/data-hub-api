#!/bin/bash -xe
python /app/manage.py migrate
python /app/manage.py collectstatic --noinput
python /app/manage.py runserver_plus 0.0.0.0:8000
