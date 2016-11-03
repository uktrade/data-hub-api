#!/bin/bash -xe
python /app/leeloo/manage.py migrate
python /app/leeloo/manage.py collectstatic --noinput
python /app/leeloo/manage.py loaddata /app/leeloo/fixtures/undefined.yaml
python /app/leeloo/manage.py loaddata /app/leeloo/fixtures/datahub_businesstypes.yaml
python /app/leeloo/manage.py loaddata /app/leeloo/fixtures/metadata.yaml
gunicorn datahubapi.wsgi --bind=0.0.0.0:8000
