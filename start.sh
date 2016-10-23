#!/bin/bash -xe
python /app/leeloo/manage.py migrate
python /app/leeloo/manage.py createinitialrevisions
python /app/leeloo/manage.py runserver_plus 0.0.0.0:8000
