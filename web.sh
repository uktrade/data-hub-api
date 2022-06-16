#!/usr/bin/env bash

# Start-up script for the web process, primarily for GOV.UK PaaS (see the Procfile)

set  -xe

./manage.py distributed_migrate --noinput

# This command schedules asynchronous Celery tasks, so this checks the app instance index to
# avoid tasks being scheduled multiple times unnecessarily
# (using a similar approach to https://docs.run.pivotal.io/buildpacks/ruby/rake-config.html)
if [ -z "$SKIP_OPENSEARCH_MAPPING_MIGRATIONS" ] && [ "${CF_INSTANCE_INDEX:-0}" == "0" ]; then
  ./manage.py migrate_search
fi

python manage.py collectstatic  --noinput
python app.py
