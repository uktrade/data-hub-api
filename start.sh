#!/bin/bash -xe
python /app/manage.py migrate --noinput
python /app/manage.py migrate --database mi --noinput
python /app/manage.py init_es
python /app/manage.py collectstatic --noinput
# Run runserver in a while loop as the whole docker container will otherwise die
# when there is bad syntax
while true; do 
    python /app/manage.py runserver_plus 0.0.0.0:8000
    sleep 1
done
