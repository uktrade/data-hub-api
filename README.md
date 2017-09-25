# Data Hub Leeloo

[![image](https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master.svg?style=svg)](https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master)
[![image](https://codecov.io/gh/uktrade/data-hub-leeloo/branch/master/graph/badge.svg)](https://codecov.io/gh/uktrade/data-hub-leeloo)
[![image](https://codeclimate.com/github/uktrade/data-hub-leeloo/badges/gpa.svg)](https://codeclimate.com/github/uktrade/data-hub-leeloo)
[![Code Health](https://landscape.io/github/uktrade/data-hub-leeloo/master/landscape.svg?style=flat)](https://landscape.io/github/uktrade/data-hub-leeloo/master)
[![Updates](https://pyup.io/repos/github/uktrade/data-hub-leeloo/shield.svg)](https://pyup.io/repos/github/uktrade/data-hub-leeloo/)

Leeloo provides an API into Data Hub for Data Hub clients. Using Leeloo you can search for entities and manage companies, contacts and interactions.

## Installation with Docker

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
    docker-compose run leeloo python manage.py loadmetadata
    docker-compose run leeloo python manage.py load_omis_metadata
    docker-compose run leeloo python manage.py createinitialrevisions
    ```
4. Optionally, you can load some test data and update elasticsearch:

    ```shell
    docker-compose run leeloo python manage.py loaddata /app/fixtures/test_data.yaml

    docker-compose run leeloo python manage.py sync_es
    ```

5.  Create a superuser:

    ```shell
    docker-compose run leeloo python manage.py createsuperuser
    ```

6.  Run the services:

    ```shell
    docker-compose up
    ```

## Local development with Docker

To run the tests:

```shell
docker-compose run leeloo bash tests.sh
docker-compose run leeloo bash tests-auth.sh
```

To run the linter:

```shell
docker-compose run leeloo flake8
```

## Native installation (without Docker)

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

8. Make sure you have elasticsearch running locally. If you don't, you can run one in docker:

    ```shell
    docker run -p 9200:9200 -e "http.host=0.0.0.0" -e "transport.host=127.0.0.1" elasticsearch:2.3
    ```

9.  Configure and populate the db:

    ```shell
    ./manage.py migrate
    ./manage.py createsuperuser

    ./manage.py loadmetadata
    ./manage.py load_omis_metadata
    ./manage.py createinitialrevisions
    ```

10. Optionally, you can load some test data and update elasticsearch:

    ```shell
    ./manage.py loaddata fixtures/test_data.yaml

    ./manage.py sync_es
    ```

11. Start the server:

    ```shell
    ./manage.py runserver
    ```

## Local development (without Docker)

To run the tests:

```shell
bash tests.sh
bash tests-auth.sh
```

To run the linter:

```shell
flake8
```

## Granting access to the front end

To give access to the [internal front end](https://github.com/uktrade/data-hub-frontend):

1. Log into the [Django admin applications page](http://localhost:8000/admin/oauth2_provider/application/) and add a new OAuth application with these details:

    * Client type: Confidential
    * Authorization grant type: Resource owner password-based

1. Define the required scopes for the app by adding a new record in the 
[OAuth application scopes](http://localhost:8000/admin/oauth/oauthapplicationscope/) 
page with these details:
    * Application: The application just created
    * Scope: `internal-front-end`

1. Add the client ID and secret to the front-end environment variables

## Granting access to machine-to-machine clients

To give access to a machine-to-machine client that doesn't require user authentication: 

1. Log into the [Django admin applications page](http://localhost:8000/admin/oauth2_provider/application/) and add a new OAuth application with these details:

    * Client type: Confidential
    * Authorization grant type: Client credentials

1. Define the required scopes for the app by adding a new record in the 
[OAuth application scopes](http://localhost:8000/admin/oauth/oauthapplicationscope/) 
page with these details:
    * Application: The application just created
    * Scope: The required scopes

The currently defined scopes can be found in [`datahub/oauth/scopes.py`](https://github.com/uktrade/data-hub-leeloo/tree/develop/datahub/oauth/scopes.py).

[Further information about the available grant types can be found in the OAuthLib docs](http://oauthlib.readthedocs.io/en/stable/oauth2/grants/grants.html).

## Deployment

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

## Management commands

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
docker-compose run leeloo python manage.py loadmetadata
docker-compose run leeloo python manage.py load_omis_metadata
```

Update Elasticsearch:

```shell
docker-compose run leeloo python manage.py sync_es
```

## Dependencies

Direct dependencies are specified in `requirements.in`. `requirements.txt` is a lock file generated using [pip-compile (from pip-tools)](https://github.com/jazzband/pip-tools) and should not be manually edited.

To update the lock file and indirect dependencies, run:

```shell
pip-compile --upgrade --output-file requirements.txt requirements.in
```

This must be run whenever `requirements.in` is edited.

Dependencies should still be installed using `requirements.txt`.
