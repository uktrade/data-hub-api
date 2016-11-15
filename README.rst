===================
Leeloo Data Hub API
===================

.. image:: https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master.svg?style=svg
    :target: https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master


Leeloo provides an API into Datahub for Datahub clients. Using Leeloo you can search for entities
and manage companies, contacts and interactions.

Installation
------------

Leeloo uses Docker compose to setup and run all the necessary components.
The docker-compose.yaml file provided is meant to be used for running tests. Refer to the main repo for the development and live Docker Compose file.


Build and run the necessary containers for the required environment::

    docker-compose up --build


Management commands
-------------------

If the database is freshly built or a new versioned model is added run::

    docker-compose run leeloo python manage.py createinitialrevisions

Load metadata::

    docker-compose run leeloo python manage.py loaddata /app/fixtures/metadata.yaml
    docker-compose run leeloo python manage.py loaddata /app/leeloo/undefined.yaml
    docker-compose run leeloo python manage.py loaddata /app/fixtures/datahub_businesstypes.yaml

Apply migrations::
    
    docker-compose run leeloo python manage.py migrate
    