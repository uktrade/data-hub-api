from unittest import mock

import pytest
import requests
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.timezone import now
from oauth2_provider.models import Application
from rest_framework import status

from datahub.core import constants
from datahub.metadata.models import Team

pytestmark = pytest.mark.django_db

"""Test case to cover authentication scenarios.

1) User exists in CDMS and it's whitelisted, bad credentials case
2) User exists in CDMS and it's whitelisted, correct credentials case
3) User exists in CDMS but it's not whitelisted
4) User doesn't exist in CDMS, but it does in Django

All the users have the flag is_active=True, CDMS users also have the password set to unusable.
"""


def get_cdms_user():
    """Return the cdms user."""
    user_model = get_user_model()
    team, _ = Team.objects.get_or_create(
        id=constants.Team.undefined.value.id,
        name=constants.Team.undefined.value.name
    )
    try:
        user = user_model.objects.get(email='cdms@user.com')
    except user_model.DoesNotExist:
        user = user_model(
            first_name='CDMS',
            last_name='User',
            email='cdms@user.com',
            date_joined=now(),
            dit_team=team
        )
        user.set_unusable_password()
        user.save(as_korben=True)
    return user


def get_django_user():
    """Return the django user."""
    user_model = get_user_model()
    team, _ = Team.objects.get_or_create(
        id=constants.Team.undefined.value.id,
        name=constants.Team.undefined.value.name
    )
    try:
        user = user_model.objects.get(email='django@user.com')
    except user_model.DoesNotExist:
        user = user_model(
            first_name='Django',
            last_name='User',
            email='django@user.com',
            date_joined=now(),
            dit_team=team
        )
        user.set_password('foobar')
        user.save(as_korben=True)
    return user


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.korben_authenticate')
def test_invalid_cdms_credentials(korben_auth_mock, settings, live_server):
    """Test login invalid cdms credentials."""
    settings.DIT_ENABLED_ADVISORS = ('cdms@user.com',)
    korben_auth_mock.return_value = False
    cdms_user = get_cdms_user()
    application, _ = Application.objects.get_or_create(
        user=cdms_user,
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
        name='Test auth client'
    )
    url = live_server + reverse('token')
    auth = requests.auth.HTTPBasicAuth(application.client_id, application.client_secret)
    response = requests.post(
        url,
        data={'grant_type': 'password', 'username': cdms_user.email, 'password': cdms_user.password},
        auth=auth
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Invalid credentials given' in response.text


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.korben_authenticate')
def test_valid_cdms_credentials(korben_auth_mock, settings, live_server):
    """Test login valid cdms credentials."""
    settings.DIT_ENABLED_ADVISORS = ('cdms@user.com',)
    korben_auth_mock.return_value = True
    cdms_user = get_cdms_user()
    application, _ = Application.objects.get_or_create(
        user=cdms_user,
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
        name='Test auth client'
    )
    url = live_server + reverse('token')
    auth = requests.auth.HTTPBasicAuth(application.client_id, application.client_secret)
    response = requests.post(
        url,
        data={'grant_type': 'password', 'username': cdms_user.email, 'password': cdms_user.password},
        auth=auth
    )
    assert response.status_code == status.HTTP_200_OK
    assert '"token_type": "Bearer"' in response.text


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.korben_authenticate')
def test_valid_cdms_credentials_user_not_whitelisted(korben_auth_mock, settings, live_server):
    """Test login valid cdms credentials, but user not whitelisted."""
    settings.DIT_ENABLED_ADVISORS = ()
    korben_auth_mock.return_value = True
    cdms_user = get_cdms_user()
    application, _ = Application.objects.get_or_create(
        user=cdms_user,
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
        name='Test auth client'
    )
    url = live_server + reverse('token')
    auth = requests.auth.HTTPBasicAuth(application.client_id, application.client_secret)
    response = requests.post(
        url,
        data={'grant_type': 'password', 'username': cdms_user.email, 'password': cdms_user.password},
        auth=auth
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Invalid credentials given' in response.text


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.korben_authenticate')
def test_valid_django_user(korben_auth_mock, live_server):
    """Test login valid Django credentials."""
    korben_auth_mock.return_value = False
    django_user = get_django_user()
    application, _ = Application.objects.get_or_create(
        user=django_user,
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
        name='Test auth client'
    )
    url = live_server + reverse('token')
    auth = requests.auth.HTTPBasicAuth(application.client_id, application.client_secret)
    response = requests.post(
        url,
        data={'grant_type': 'password', 'username': django_user.email, 'password': 'foobar'},
        auth=auth
    )
    assert response.status_code == status.HTTP_200_OK
    assert '"token_type": "Bearer"' in response.text
