#!/usr/bin/env bash

# Start-up script for the web process, primarily for GOV.UK PaaS (see the Procfile)

set  -xe

./manage.py distributed_migrate --noinput

if [ -z "$SKIP_MI_DATABASE_MIGRATIONS" ]; then
  ./manage.py distributed_migrate --noinput --database mi
fi

# This command schedules asynchronous Celery tasks, so this checks the app instance index to
# avoid tasks being scheduled multiple times unnecessarilly
# (using a similar approach to https://docs.run.pivotal.io/buildpacks/ruby/rake-config.html)
if [ -z "$SKIP_ES_MAPPING_MIGRATIONS" ] && [ "${CF_INSTANCE_INDEX:-0}" == "0" ]; then
  ./manage.py migrate_es
fi

gunicorn config.wsgi --config config/gunicorn.py
