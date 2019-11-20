#!/bin/bash -xe
# This file is used as a cmd script with an automatically built backend docker to run User Acceptance Tests against
# on circleCI. For more information about how this is used please see
# https://github.com/uktrade/data-hub-frontend#continuous-integration

dockerize -wait ${POSTGRES_URL} -wait ${MI_POSTGRES_URL} -wait ${ES5_URL} -timeout 120s
python /app/manage.py migrate
python /app/manage.py migrate --database mi
python /app/manage.py init_es
python /app/manage.py loadinitialmetadata

# TODO abstract this into a method in ./manage.py
echo "import datetime
from django.contrib.auth.models import Group
from django.utils.timezone import now
from oauth2_provider.models import AccessToken
from datahub.company.models import Advisor

dit_east_midlands_id = '9010dd28-9798-e211-a939-e4115bead28a'

dit_staff_user = Advisor.objects.create_user(
    email='dit_staff@datahub.com',
    first_name='DIT',
    last_name='Staff',
    dit_team_id=dit_east_midlands_id,
)

AccessToken.objects.create(
    user=dit_staff_user,
    token='ditStaffToken',
    expires=now() + datetime.timedelta(days=1),
    scope='data-hub:internal-front-end',
)

welsh_government_id = 'bc85aa17-fabd-e511-88b6-e4115bead28a'

da_staff_user = Advisor.objects.create_user(
    email='da_staff@datahub.com',
    first_name='DA',
    last_name='Staff',
    dit_team_id=welsh_government_id,
)

AccessToken.objects.create(
    user=da_staff_user,
    token='daStaffToken',
    expires=now() + datetime.timedelta(days=1),
    scope='data-hub:internal-front-end',
)

heart_of_the_south_west_lep_id = '08d987f8-6525-e511-b6bc-e4115bead28a'

lep_staff_user = Advisor.objects.create_user(
    email='lep_staff@datahub.com',
    first_name='LEP',
    last_name='Staff',
    dit_team_id=heart_of_the_south_west_lep_id,
)

AccessToken.objects.create(
    user=lep_staff_user,
    token='lepStaffToken',
    expires=now() + datetime.timedelta(days=1),
    scope='data-hub:internal-front-end',
)
" | /app/manage.py shell

python /app/manage.py loaddata /app/fixtures/test_data.yaml
python /app/manage.py createinitialrevisions
python /app/manage.py sync_es --foreground
python /app/manage.py collectstatic --noinput
DEBUG=False gunicorn config.wsgi --config config/gunicorn.py -b 0.0.0.0
