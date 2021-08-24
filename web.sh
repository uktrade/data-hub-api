#!/usr/bin/env bash

# Start-up script for the web process, primarily for GOV.UK PaaS (see the Procfile)

set  -xe

# Django 3.2 upgrade commands

./manage.py rename_apps || true
./manage.py distributed_migrate omis_region 0002_alter_ukregionalsettings_table --fake
./manage.py distributed_migrate omis_payment 0009_auto_20210816_1601 --fake
./manage.py distributed_migrate omis_market 0002_alter_market_table --fake
./manage.py distributed_migrate omis_invoice 0013_alter_invoice_table --fake
./manage.py distributed_migrate omis_quote 0009_auto_20210816_1601 --fake

./manage.py distributed_migrate --noinput

# This command schedules asynchronous Celery tasks, so this checks the app instance index to
# avoid tasks being scheduled multiple times unnecessarily
# (using a similar approach to https://docs.run.pivotal.io/buildpacks/ruby/rake-config.html)
if [ -z "$SKIP_ES_MAPPING_MIGRATIONS" ] && [ "${CF_INSTANCE_INDEX:-0}" == "0" ]; then
  ./manage.py migrate_es
fi

gunicorn config.wsgi --config config/gunicorn.py
