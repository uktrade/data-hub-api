#!/bin/bash -xe
# This file is used as a cmd script with an automatically built backend docker to run User Acceptance Tests against on circleCI.
# For more information about how this is used please see https://github.com/uktrade/data-hub-frontend

dockerize -wait ${POSTGRES_URL} -wait ${ES5_URL} -timeout 60s
python /app/manage.py migrate
python /app/manage.py loadmetadata
python /app/manage.py load_omis_metadata

echo "from oauth2_provider.models import Application;
from datahub.oauth.models import OAuthApplicationScope;
app = Application.objects.create(
    name='circleci',
    client_id='${API_CLIENT_ID}',
    client_secret='${API_CLIENT_SECRET}',
    client_type=Application.CLIENT_CONFIDENTIAL,
    authorization_grant_type=Application.GRANT_PASSWORD
);
OAuthApplicationScope.objects.create(application=app, scopes=['internal-front-end'])" | /app/manage.py shell

echo "from datahub.company.models import Advisor;
Advisor.objects.create_user(
    email='${QA_USER_EMAIL}',
    password='${QA_USER_PASSWORD}',
    first_name='Circle',
    last_name='Ci'
)" | /app/manage.py shell

python /app/manage.py loaddata /app/fixtures/test_ch_data.yaml
python /app/manage.py loaddata /app/fixtures/test_data.yaml
python /app/manage.py createinitialrevisions
python /app/manage.py sync_es
python /app/manage.py runserver 0.0.0.0:8000
