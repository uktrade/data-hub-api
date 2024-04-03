#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

# Add commands below to run inside the container after all the other buildpacks have been applied
export ADMIN_OAUTH2_ENABLED="True"
export ADMIN_OAUTH2_BASE_URL=""
export ADMIN_OAUTH2_TOKEN_FETCH_PATH="/o/token/"
export ADMIN_OAUTH2_USER_PROFILE_PATH="/o/v1/user/me/"
export ADMIN_OAUTH2_AUTH_PATH="/o/authorize/"
export ADMIN_OAUTH2_CLIENT_ID="client-id"
export ADMIN_OAUTH2_CLIENT_SECRET="client-secret"
export ADMIN_OAUTH2_LOGOUT_PATH="/o/logout"
export ACTIVITY_STREAM_ACCESS_KEY_ID="some-id"
export ACTIVITY_STREAM_SECRET_ACCESS_KEY="some-secret"
export DATABASE_URL="postgresql://postgres:datahub@postgres/datahub"
export DEBUG="True"
export DJANGO_SECRET_KEY="changeme"
export DJANGO_SETTINGS_MODULE="config.settings.local"
export ES_INDEX_PREFIX="test_index"
export ES5_URL="http://localhost:9200"
export OPENSEARCH_URL="http://localhost:9200"
export OPENSEARCH_INDEX_PREFIX="test_index"
export PAAS_IP_ALLOWLIST="1.2.3.4"
export AWS_DEFAULT_REGION="eu-west-2"
export AWS_ACCESS_KEY_ID="foo"
export AWS_SECRET_ACCESS_KEY="bar"
export DEFAULT_BUCKET="baz"
export SSO_ENABLED="True"
export STAFF_SSO_BASE_URL="http://sso.invalid/"
export STAFF_SSO_AUTH_TOKEN="sso-token"
export DIT_EMAIL_DOMAINS="trade.gov.uk,digital.trade.gov.uk"
export DATA_HUB_FRONTEND_ACCESS_KEY_ID="frontend-key-id"
export DATA_HUB_FRONTEND_SECRET_ACCESS_KEY="frontend-key"
export ES_APM_ENABLED="False"
export ES_APM_SERVICE_NAME="datahub"
export ES_APM_SECRET_TOKEN=""
export ES_APM_SERVER_URL="http://localhost:8200"
export ES_APM_ENVIRONMENT="circleci"
export REDIS_BASE_URL="redis://localhost:6379"

python manage.py collectstatic  --noinput
