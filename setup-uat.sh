#!/bin/bash -xe
# This file is used as a cmd script with an automatically built backend docker to run User Acceptance Tests against on circleCI.
# For more information about how this is used please see https://github.com/uktrade/data-hub-frontend

dockerize -wait ${POSTGRES_URL} -wait ${ES5_URL} -timeout 60s
python /app/manage.py migrate
python /app/manage.py loadmetadata
python /app/manage.py load_omis_metadata

echo "import datetime
from oauth2_provider.models import AccessToken
from django.utils.timezone import now
from datahub.company.models import Advisor

user = Advisor.objects.create_user(
    email='${QA_USER_EMAIL}',
    first_name='Circle',
    last_name='Ci'
)

AccessToken.objects.create(
    user=user,
    token='${OAUTH2_DEV_TOKEN}',
    expires=now() + datetime.timedelta(days=1),
    scope='data-hub:internal-front-end'
)" | /app/manage.py shell

python /app/manage.py loaddata /app/fixtures/test_ch_data.yaml
python /app/manage.py loaddata /app/fixtures/test_data.yaml
python /app/manage.py createinitialrevisions
python /app/manage.py sync_es
python /app/manage.py runserver 0.0.0.0:8000
