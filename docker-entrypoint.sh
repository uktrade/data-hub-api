#!/bin/bash -xe
mkdir /usr/src/app/datahubapi/static
mkdir /usr/src/app/datahubapi/staticfiles
python /usr/src/app/manage.py migrate                  # Apply database migrations
python /usr/src/app/manage.py collectstatic --noinput  # Collect static files


# Start Gunicorn processes
echo Starting Gunicorn.
gunicorn -c /usr/src/app/gunicorn/conf.py datahubapi.wsgi --log-file - -b [::1]:8000 -b 0.0.0.0:8000
