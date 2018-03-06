# Data Hub Leeloo

[![image](https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master.svg?style=svg)](https://circleci.com/gh/uktrade/data-hub-leeloo/tree/master)
[![image](https://codecov.io/gh/uktrade/data-hub-leeloo/branch/master/graph/badge.svg)](https://codecov.io/gh/uktrade/data-hub-leeloo)
[![image](https://codeclimate.com/github/uktrade/data-hub-leeloo/badges/gpa.svg)](https://codeclimate.com/github/uktrade/data-hub-leeloo)
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
    docker-compose run leeloo ./manage.py migrate
    docker-compose run leeloo ./manage.py loadinitialmetadata
    docker-compose run leeloo ./manage.py createinitialrevisions
    ```
4. Optionally, you can load some test data and update elasticsearch:

    ```shell
    docker-compose run leeloo ./manage.py loaddata /app/fixtures/test_data.yaml

    docker-compose run leeloo ./manage.py sync_es
    ```

5.  Create a superuser:

    ```shell
    docker-compose run leeloo ./manage.py createsuperuser
    ```

6.  Run the services:

    ```shell
    docker-compose up
    ```

## Native installation (without Docker)

Dependencies:

-   Python 3.6.x
-   PostgreSQL (tested on 9.5 and 9.6)
-   redis 3.2

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

8. Make sure you have Elasticsearch running locally. If you don't, you can run one in Docker:

    ```shell
    docker run -p 9200:9200 -e "http.host=0.0.0.0" -e "transport.host=127.0.0.1" elasticsearch:5.5
    ```

9. Make sure you have redis running locally and that the REDIS_URL in your `.env` is up-to-date.

10.  Configure and populate the db:

    ```shell
    ./manage.py migrate
    ./manage.py createsuperuser

    ./manage.py loadinitialmetadata
    ./manage.py createinitialrevisions
    ```

11. Optionally, you can load some test data and update Elasticsearch:

    ```shell
    ./manage.py loaddata fixtures/test_data.yaml

    ./manage.py sync_es
    ```

12. Start the server:

    ```shell
    ./manage.py runserver
    ```

## Local development

If using Docker, prefix these commands with `docker-compose run leeloo`.

To run the tests:

```shell
./tests.sh
```

To run the tests in parallel, pass `-n <number of processes>` to `./tests.sh`. For example, for four processes:


```shell
./tests.sh -n 4
```


To run the linter:

```shell
flake8
```

## Granting access to the front end

The [internal front end](https://github.com/uktrade/data-hub-frontend) uses single sign-on. You should configure Leeloo as follows to use with the front end:

* `SSO_ENABLED`: `True`
* `RESOURCE_SERVER_INTROSPECTION_URL`: URL of the [RFC 7662](https://tools.ietf.org/html/rfc7662) introspection endpoint (should be the same server the front end is using). This is provided by a [Staff SSO](https://github.com/uktrade/staff-sso) instance.
* `RESOURCE_SERVER_AUTH_TOKEN`: Access token for the introspection server.

The token should have the `data-hub:internal-front-end` scope. django-oauth-toolkit will create a user corresponding to the token if one does not already exist.

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

Leeloo can run on any Heroku-style platform. Configuration is performed via the following environment variables:


| Variable name | Required | Description |
| ------------- | ------------- | ------------- |
| `AV_SERVICE_URL` | Yes | URL for ClamAV service. If not configured, virus scanning will fail. |
| `AWS_ACCESS_KEY_ID` | No | Used as part of [boto3 auto-configuration](http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials). |
| `AWS_DEFAULT_REGION` | No | [Default region used by boto3.](http://boto3.readthedocs.io/en/latest/guide/configuration.html#environment-variable-configuration) |
| `AWS_SECRET_ACCESS_KEY` | No | Used as part of [boto3 auto-configuration](http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials). |
| `BULK_INSERT_BATCH_SIZE`  | No | Used when loading Companies House records (default=5000). |
| `DATABASE_URL`  | Yes | PostgreSQL server URL (with embedded credentials). |
| `DATAHUB_FRONTEND_BASE_URL`  | Yes | |
| `DATAHUB_SECRET`  | Yes | |
| `DEBUG`  | Yes | Whether Django's debug mode should be enabled. |
| `DJANGO_SECRET_KEY`  | Yes | |
| `DJANGO_SENTRY_DSN`  | Yes | |
| `DJANGO_SETTINGS_MODULE`  | Yes | |
| `DOCUMENTS_BUCKET`  | Yes | S3 bucket for document storage. |
| `ES_INDEX`  | Yes | |
| `ES_URL`  | Yes | |
| `ES_VERIFY_CERTS`  | No | |
| `GUNICORN_ACCESSLOG`  | No | File to direct Gunicorn logs to (default=stdout). |
| `GUNICORN_ACCESS_LOG_FORMAT`  | No |  |
| `GUNICORN_WORKER_CLASS`  | No | [Type of Gunicorn worker.](http://docs.gunicorn.org/en/stable/settings.html#worker-class) Uses async workers via gevent by default. |
| `GUNICORN_WORKER_CONNECTIONS`  | No | Maximum no. of connections for async workers (default=10). |
| `OMIS_NOTIFICATION_ADMIN_EMAIL`  | Yes | |
| `OMIS_NOTIFICATION_API_KEY`  | Yes | |
| `OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL`  | No | |
| `OMIS_PUBLIC_BASE_URL`  | Yes | |
| `RESOURCE_SERVER_INTROSPECTION_URL` | If SSO enabled | RFC 7662 token introspection URL used for signle sign-on |
| `RESOURCE_SERVER_AUTH_TOKEN` | If SSO enabled | Access token for RFC 7662 token introspection server |
| `SENTRY_ENVIRONMENT`  | Yes | Value for the environment tag in Sentry. |
| `SSO_ENABLED` | Yes | Whether single sign-on via RFC 7662 token introspection is enabled |
| `WEB_CONCURRENCY` | No | Number of Gunicorn workers (set automatically by Heroku, otherwise defaults to 1). |


## Management commands

If using Docker, remember to run these commands inside your container by prefixing them with `docker-compose run leeloo`.

### Database


#### Apply migrations

```shell
./manage.py migrate
```

#### Create django-reversion initial revisions

If the database is freshly built or a new versioned model is added run:

```shell
./manage.py createinitialrevisions
```

#### Load initial metadata

These commands are generally only intended to be used on a blank database.

```shell
./manage.py loadinitialmetadata
```


### Elasticsearch

Resync all Elasticsearch records:

```shell
./manage.py sync_es
```

You can resync only specific models by using the `--model=` argument.

```shell
./manage.py sync_es --model=company --model=contact
```

For more details including all the available choices:

```shell
./manage.py sync_es --help
```

### Companies House

Update Companies House records:

```shell
./manage.py sync_ch
```

This downloads the latest data from Companies House, updates the Companies House table and triggers an Elasticsearch sync.

(Note that this does not remove any records from the Companies House table.)

## Dependencies

Direct dependencies are specified in `requirements.in`. `requirements.txt` is a lock file generated using [pip-compile (from pip-tools)](https://github.com/jazzband/pip-tools) and should not be manually edited.

To update the lock file and indirect dependencies, run:

```shell
pip-compile --upgrade --output-file requirements.txt requirements.in
```

This must be run whenever `requirements.in` is edited.

Dependencies should still be installed using `requirements.txt`.
