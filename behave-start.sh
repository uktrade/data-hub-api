#!/bin/bash -xe
python /app/manage.py migrate
python /app/manage.py collectstatic --noinput
python /app/manage.py loaddata metadata.yaml
python /app/manage.py loaddata undefined.yaml
python /app/manage.py loaddata datahub_businesstypes.yaml
python /app/manage.py behaveinitialsetup
gunicorn config.wsgi
