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
The `docker-compose.yml` file provided is meant to be used for running tests. Refer to the main repo for the development and live Docker Compose file.


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
    docker-compose run leeloo python manage.py loaddata /app/fixtures/undefined.yaml
    docker-compose run leeloo python manage.py loaddata /app/fixtures/datahub_businesstypes.yaml


Architectural notes
===================

The version 2 folders structure differs from the usual Django pattern. Instead of having the code divided in apps modules,
there are the following folders: `repos`, `schemas`, `views` and `tests`.
The models are still living in their relative apps folders, but they should be moved into a `models` folder once
the migration to v2 is completed

The version 2 of the API implements the repository pattern, the main components are:

**schemas**
  they are subclasses of `colander.Schema`. Single fields validation happens here and an instance of the schema is
  used by the repo to deserialize and validate, the incoming data. The data serialisation is manually handled in
  the repo class.

**repos**
  repo classes MUST implement three methods: `get`, `filter` and `upsert`. Repos take a `config` variable when
  initialised, it's a dictionary with all the necessary configuration settings. At the moment our repos are a
  wrapper around the Django ORM, this is the reason why any cross fields validation that relies on database
  access happens in the repo.

Other components are required by Django and DRF, they are views, renderers and parsers.

**parsers**
  the parser class MUST implement the `parse` method, it also enforces the media type and some basic data structure validation.

**renderers**
  the render class MUST implement the `render` method. It handles the rendering and it's in charge of rendering
  the exceptions in the correct format.

The response-request flow happens in this way: the request hits the parser class, which does some basic checks.
Then the data is passed to the view which calls the correct repo class method passing the data through.
The repo class does the schema validation and any other validation, raising the correct type of error if necessary.
The repo handles the serialisation, returning the data in the right format back to the view.
The view then passes the correctly serialised data to the renderer class, which then generates the response.
