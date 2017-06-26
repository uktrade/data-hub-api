[![image](https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master.svg?style=svg)](https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master)
[![image](https://codecov.io/gh/uktrade/data-hub-leeloo/branch/master/graph/badge.svg)](https://codecov.io/gh/uktrade/data-hub-leeloo)
[![image](https://codeclimate.com/github/uktrade/data-hub-leeloo/badges/gpa.svg)](https://codeclimate.com/github/uktrade/data-hub-leeloo)
[![Code Health](https://landscape.io/github/uktrade/data-hub-leeloo/master/landscape.svg?style=flat)](https://landscape.io/github/uktrade/data-hub-leeloo/master)
[![Updates](https://pyup.io/repos/github/uktrade/data-hub-leeloo/shield.svg)](https://pyup.io/repos/github/uktrade/data-hub-leeloo/)

Leeloo provides an API into Data Hub for Data Hub clients. Using Leeloo you can search for entities and manage companies, contacts and interactions.

Installation with Docker
========================

Leeloo uses Docker compose to setup and run all the necessary components. The docker-compose.yml file provided is meant to be used for running tests and development.

1.  Clone the repository:

    ```shell
    git clone https://github.com/uktrade/data-hub-leeloo
    cd data-hub-leeloo
    ```

2.  Build and run the necessary containers for the required environment:

    ```shell
    docker-compose build
    ```

3.  Populate the db:

    ```shell
    docker-compose run leeloo python manage.py migrate
    docker-compose run leeloo python manage.py loaddata /app/fixtures/metadata.yaml
    docker-compose run leeloo python manage.py loaddata /app/fixtures/datahub_businesstypes.yaml
    docker-compose run leeloo python manage.py createinitialrevisions
    ```

4.  Create a superuser:

    ```shell
    docker-compose run leeloo python manage.py createsuperuser
    ```

5.  Run the services:

    ```shell
    docker-compose up
    ```

6.  To set up the [data hub frontend app](https://github.com/uktrade/data-hub-fe-beta2), log into the [django admin](http://localhost:8000/admin/oauth2_provider/application/) and add a new oauth application with:

        - Client type: Confidential
        - Authorization grant type: Resource owner password-based

7.  Add the client id / client secret to the frontend .env file

Local development with Docker
-----------------------------

To run the tests:

```shell
docker-compose run leeloo bash tests.sh
docker-compose run leeloo bash tests-auth.sh
```

To run the linter:

```shell
docker-compose run leeloo flake8
```

Native installation (without Docker)
====================================

Dependencies:

-   Python 3.6.1
-   Postgres (tested on 9.5+)

1.  Clone the repository:

    ```shell
    git clone https://github.com/uktrade/data-hub-leeloo
    cd data-hub-leeloo
    ```

2.  Install `virtualenv` if you don’t have it already:

    ```shell
    pip install virtualenv
    ```

3.  Create and activate the virtualenv:

    ```shell
    virtualenv --python=python3 env
    source env/bin/activate
    pip install -U pip
    ```

4.  Install the dependencies:

    ```shell
    pip install -r requirements.txt
    ```

5.  Create an `.env` settings file (it’s gitignored by default):

    ```shell
    cp config/settings/sample.env config/settings/.env
    ```

6.  Set `DOCKER_DEV=False` in `.env`
7.  Create the db. By default, the dev version uses postgres:

    ```shell
    psql -p5432
    create database datahub;
    ```

8.  Configure and populate the db:

    ```shell
    ./manage.py migrate
    ./manage.py createsuperuser
    
    ./manage.py loaddata fixtures/metadata.yaml
    ./manage.py loaddata fixtures/datahub_businesstypes.yaml
    ./manage.py createinitialrevisions
    ```

9.  Start the server:

    ```shell
    ./manage.py runserver
    ```

10. To set up the [data hub frontend app](https://github.com/uktrade/data-hub-fe-beta2), log into the [django admin](http://localhost:8000/admin/oauth2_provider/application/) and add a new oauth application with:

        - Client type: Confidential
        - Authorization grant type: Resource owner password-based

11. Add the client id / client secret to the frontend .env file

Local development (without Docker)
----------------------------------

To run the tests:

```shell
bash tests.sh
bash tests-auth.sh
```

To run the linter:

```shell
flake8
```

Heroku
======

Leeloo can run on any Heroku style platform. These environment variables MUST be configured:

-   DATABASE\_URL
-   DATAHUB\_SECRET
-   DEBUG
-   DJANGO\_SECRET\_KEY
-   DJANGO\_SENTRY\_DSN
-   DJANGO\_SETTINGS\_MODULE
-   BULK\_CREATE\_BATCH\_SIZE (default=5000)
-   ES\_URL
-   ES\_INDEX
-   AWS\_ACCESS\_KEY\_ID
-   AWS\_SECRET\_ACCESS\_KEY
-   DOCUMENTS\_BUCKET

Management commands
===================

Enable CDMS login for users (use this to let a CDMS user log in):

```shell
docker-compose run leeloo python manage.py manageusers test@bar.com foo@bar.com --enable
```

Disable CDMS login for users:

```shell
docker-compose run leeloo python manage.py manageusers test@bar.com foo@bar.com --disable
```

Apply migrations:

```shell
docker-compose run leeloo python manage.py migrate
```

If the database is freshly built or a new versioned model is added run:

```shell
docker-compose run leeloo python manage.py createinitialrevisions
```

Load metadata:

```shell
docker-compose run leeloo python manage.py loaddata /app/fixtures/metadata.yaml
docker-compose run leeloo python manage.py loaddata /app/fixtures/datahub_businesstypes.yaml
```

Dependencies
============

Direct dependencies are specified in `requirements.in`. `requirements.txt` is a lock file generated using [pip-compile (from pip-tools)](https://github.com/jazzband/pip-tools) and should not be manually edited.

To update the lock file and indirect dependencies, run:

```shell
pip-compile --upgrade --output-file requirements.txt requirements.in
```

This must be run whenever `requirements.in` is edited.

Dependencies should still be installed using `requirements.txt`.
