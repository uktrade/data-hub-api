===================
Leeloo Data Hub API
===================

.. image:: https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master.svg?style=svg
    :target: https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master

.. image:: https://codecov.io/gh/uktrade/data-hub-leeloo/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/uktrade/data-hub-leeloo

.. image:: https://codeclimate.com/github/uktrade/data-hub-leeloo/badges/gpa.svg
    :target: https://codeclimate.com/github/uktrade/data-hub-leeloo

.. image:: https://landscape.io/github/uktrade/data-hub-leeloo/master/landscape.svg?style=flat
   :target: https://landscape.io/github/uktrade/data-hub-leeloo/master
   :alt: Code Health

.. image:: https://pyup.io/repos/github/uktrade/data-hub-leeloo/shield.svg
     :target: https://pyup.io/repos/github/uktrade/data-hub-leeloo/
     :alt: Updates


Leeloo provides an API into Datahub for Datahub clients. Using Leeloo you can search for entities
and manage companies, contacts and interactions.

Installation with Docker
------------------------

Leeloo uses Docker compose to setup and run all the necessary components.
The `docker-compose.yml` file provided is meant to be used for running tests and development.

#. Clone the repository::

    git clone https://github.com/uktrade/data-hub-leeloo
    cd data-hub-leeloo

#. Build and run the necessary containers for the required environment::


    docker-compose build

#. Populate the db::

    docker-compose run leeloo python manage.py migrate
    docker-compose run leeloo python manage.py loaddata /app/fixtures/metadata.yaml
    docker-compose run leeloo python manage.py loaddata /app/fixtures/datahub_businesstypes.yaml
    docker-compose run leeloo python manage.py createinitialrevisions

#. Create a superuser::

    docker-compose run leeloo python manage.py createsuperuser

#. Run the services::

    docker-compose up

#. To set up the `data hub frontend app <https://github.com/uktrade/data-hub-fe-beta2>`_,
   log into the `django admin <http://localhost:8000/admin/oauth2_provider/application/>`_ and add a new oauth application with::

    - Client type: Confidential
    - Authorization grant type: Resource owner password-based

#. Add the client id / client secret to the frontend `.env` file


Local development with Docker
:::::::::::::::::::::::::::::

To run the tests::

    docker-compose run leeloo bash tests.sh
    docker-compose run leeloo bash tests-auth.sh

To run the linter::

    docker-compose run leeloo flake8


Native installation (without Docker)
------------------------------------

Dependencies:

- Python 3.6.1
- Postgres (tested on 9.5+)


#. Clone the repository::

    git clone https://github.com/uktrade/data-hub-leeloo
    cd data-hub-leeloo

#. Install ``virtualenv`` if you don’t have it already::

    pip install virtualenv

#. Create and activate the virtualenv::

    virtualenv --python=python3 env
    source env/bin/activate
    pip install -U pip

#. Install the dependencies::

    pip install -r requirements.txt

#. Create an ``.env`` settings file (it’s gitignored by default)::

    cp config/settings/sample.env config/settings/.env

#. Set ``DOCKER_DEV=False`` in ``.env``

#. Create the db. By default, the dev version uses postgres::

    psql -p5432
    create database datahub;

#. Configure and populate the db::

    ./manage.py migrate
    ./manage.py createsuperuser

    ./manage.py loaddata fixtures/metadata.yaml
    ./manage.py loaddata fixtures/datahub_businesstypes.yaml
    ./manage.py createinitialrevisions

#. Start the server::

    ./manage.py runserver

#. To set up the `data hub frontend app <https://github.com/uktrade/data-hub-fe-beta2>`_,
   log into the `django admin <http://localhost:8000/admin/oauth2_provider/application/>`_ and add a new oauth application with::

    - Client type: Confidential
    - Authorization grant type: Resource owner password-based


#. Add the client id / client secret to the frontend .env file


Local development (without Docker)
::::::::::::::::::::::::::::::::::

To run the tests::

  bash tests.sh
  bash tests-auth.sh

To run the linter::

  flake8

Heroku
------

Leeloo can run on any Heroku style platform. These environment variables MUST be configured:

- DATABASE_URL
- DATAHUB_SECRET
- DEBUG
- DJANGO_SECRET_KEY
- DJANGO_SENTRY_DSN
- DJANGO_SETTINGS_MODULE
- BULK_CREATE_BATCH_SIZE (default=50000)
- ES_HOST
- ES_PORT
- ES_INDEX


Management commands
-------------------

Enable users to login::

    docker-compose run leeloo python manage.py manageusers test@bar.com foo@bar.com --enable

Disable users to login::

    docker-compose run leeloo python manage.py manageusers test@bar.com foo@bar.com --disable


Apply migrations::

    docker-compose run leeloo python manage.py migrate


If the database is freshly built or a new versioned model is added run::


    docker-compose run leeloo python manage.py createinitialrevisions


Load metadata::


    docker-compose run leeloo python manage.py loaddata /app/fixtures/metadata.yaml
    docker-compose run leeloo python manage.py loaddata /app/fixtures/datahub_businesstypes.yaml

Dependencies
------------
Direct dependencies are specified in ``requirements.in``. ``requirements.txt`` is a lock file generated using `pip-compile
(from pip-tools)<https://github.com/jazzband/pip-tools>`_ and should not be manually edited.

To update the lock file and indirect dependencies, run::

    pip-compile --generate-hashes --upgrade --output-file requirements.txt requirements.in

This must be run whenever ``requirements.in`` is edited.

Dependencies should still be installed using ``requirements.txt``.
