from unittest import mock

import pytest
import requests
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.metadata.models import Team

pytestmark = pytest.mark.django_db

"""Test case to cover authentication scenarios.

1) User exists in CDMS and it's whitelisted, bad credentials case
2) User exists in CDMS and it's whitelisted, correct credentials case
3) User exists in CDMS and it's whitelisted, correct credentials case, CDMS Connection fails
4) User exists in CDMS but it's not whitelisted
5) User doesn't exist in CDMS, but it does in Django
6) User exists in CDMS but password has changed

All the users have the flag is_active=True, CDMS users also have the password set to unusable.
"""

DJANGO_USER_PASSWORD = 'foobar'


def get_or_create_user(email, last_name, first_name, password=None):
    """Generic function to create or return a user.

    If password is None then it's set to unusable (CDMS user).
    """
    user_model = get_user_model()
    team, _ = Team.objects.get_or_create(
        id=constants.Team.undefined.value.id,
        name=constants.Team.undefined.value.name
    )
    try:
        user = user_model.objects.get(email=email)
    except user_model.DoesNotExist:
        user = user_model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_joined=now(),
            dit_team=team,
            enabled=True
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
    return user


def get_cdms_user():
    """Shortcut to create cdms user."""
    return get_or_create_user(
        email='cdms@user.com',
        last_name='Useri',
        first_name='CDMS'
    )


def get_django_user():
    """Shortcut to create a Django user."""
    return get_or_create_user(
        email='django@user.com',
        last_name='Useri',
        first_name='Testo',
        password=DJANGO_USER_PASSWORD
    )


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.korben_authenticate')
def test_invalid_cdms_credentials(korben_auth_mock, settings, live_server):
    """Test login invalid cdms credentials."""
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
@mock.patch('datahub.korben.connector.requests')
def test_cdms_returns_500(mocked_requests, live_server):
    """Test login when CDMS is not available."""
    mocked_requests.post.return_value = mock.Mock(ok=False)
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
def test_valid_cdms_credentials(korben_auth_mock, live_server):
    """Test login valid cdms credentials."""
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
        data={'grant_type': 'password', 'username': cdms_user.email, 'password': 'test'},
        auth=auth
    )
    assert response.status_code == status.HTTP_200_OK
    assert '"token_type": "Bearer"' in response.text

    cdms_user.refresh_from_db()

    # Validate credentials are saved
    assert cdms_user.check_password('test') is True
    assert cdms_user.is_active is True


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.korben_authenticate')
def test_valid_cdms_credentials_case_insensitive_email(korben_auth_mock, live_server):
    """Test login valid cdms credentials."""
    korben_auth_mock.return_value = True
    user = get_or_create_user(
        email='CaSeSenSitiVe@user.com',
        last_name='Sensitive',
        first_name='Case',
    )
    application, _ = Application.objects.get_or_create(
        user=user,
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
        name='Test auth client'
    )
    url = live_server + reverse('token')
    auth = requests.auth.HTTPBasicAuth(application.client_id, application.client_secret)
    response = requests.post(
        url,
        data={'grant_type': 'password', 'username': 'CaseSensiTive@user.com', 'password': 'test'},
        auth=auth
    )
    assert response.status_code == status.HTTP_200_OK
    assert '"token_type": "Bearer"' in response.text

    user.refresh_from_db()

    # Validate credentials are saved
    assert user.check_password('test') is True
    assert user.is_active is True


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.korben_authenticate')
def test_valid_cdms_credentials_and_cdms_communication_fails(korben_auth_mock, live_server):
    """Test login valid cdms credentials when CDMS communication fails."""
    korben_auth_mock.return_value = None

    # Assume user logged in previously
    cdms_user = get_cdms_user()
    cdms_user.set_password('test')
    cdms_user.is_active = True
    cdms_user.save()

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
        data={'grant_type': 'password', 'username': cdms_user.email, 'password': 'test'},
        auth=auth
    )
    assert response.status_code == status.HTTP_200_OK
    assert '"token_type": "Bearer"' in response.text


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.korben_authenticate')
def test_password_changed_in_cdms(korben_auth_mock, live_server):
    """Test passwd changed in CDMS results in failed auth."""
    korben_auth_mock.return_value = False

    # Assume user logged in previously
    cdms_user = get_cdms_user()
    cdms_user.set_password('test')
    cdms_user.is_active = True
    cdms_user.save()

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
        data={'grant_type': 'password', 'username': cdms_user.email, 'password': 'test'},
        auth=auth
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Invalid credentials given' in response.text


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.korben_authenticate')
def test_valid_cdms_credentials_user_not_whitelisted(korben_auth_mock, live_server):
    """Test login valid cdms credentials, but user not whitelisted."""
    korben_auth_mock.return_value = True
    cdms_user = get_cdms_user()
    cdms_user.enabled = False
    cdms_user.save()
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
        data={'grant_type': 'password', 'username': django_user.email, 'password': DJANGO_USER_PASSWORD},
        auth=auth
    )
    assert response.status_code == status.HTTP_200_OK
    assert '"token_type": "Bearer"' in response.text
