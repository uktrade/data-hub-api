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

Installation
------------

Leeloo uses Docker compose to setup and run all the necessary components.
The docker-compose.yaml file provided is meant to be used for running tests. Refer to the main repo for the development and live Docker Compose file.


Build and run the necessary containers for the required environment::


    docker-compose up --build


Heroku
------

Leeloo can run on any Heroku style platform. These environment variables MUST be configured:

- DATABASE_URL
- DATAHUB_SECRET
- DEBUG
- DJANGO_SECRET_KEY
- DJANGO_SENTRY_DSN
- DJANGO_SETTINGS_MODULE


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
    docker-compose run leeloo python manage.py loaddata /app/undefined.yaml
    docker-compose run leeloo python manage.py loaddata /app/fixtures/datahub_businesstypes.yaml
