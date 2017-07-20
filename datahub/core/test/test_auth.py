from unittest import mock

import pytest
import requests
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import auth

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
    try:
        user = user_model.objects.get(email=email)
    except user_model.DoesNotExist:
        user = user_model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_joined=now(),
            use_cdms_auth=True
        )
        if password:
            user.set_password(password)
            user.use_cdms_auth = False
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
@mock.patch('datahub.core.auth.CDMSUserBackend.validate_cdms_credentials')
def test_invalid_cdms_credentials(auth_mock, settings, live_server):
    """Test login invalid cdms credentials."""
    auth_mock.return_value = False
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
        data={
            'grant_type': 'password',
            'username': cdms_user.email,
            'password': cdms_user.password
        },
        auth=auth
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Invalid credentials given' in response.text


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend._cdms_login')
def test_cdms_returns_500(mocked_login, live_server):
    """Test login when CDMS is not available."""
    mocked_login.side_effect = requests.RequestException
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
        data={
            'grant_type': 'password',
            'username': cdms_user.email,
            'password': cdms_user.password
        },
        auth=auth
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Invalid credentials given' in response.text


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.validate_cdms_credentials')
def test_valid_cdms_credentials(auth_mock, live_server):
    """Test login valid cdms credentials."""
    auth_mock.return_value = True
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
@mock.patch('datahub.core.auth.CDMSUserBackend.validate_cdms_credentials')
def test_valid_cdms_credentials_case_insensitive_email(auth_mock, live_server):
    """Test login valid cdms credentials."""
    auth_mock.return_value = True
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
@mock.patch('datahub.core.auth.CDMSUserBackend.validate_cdms_credentials')
def test_valid_cdms_credentials_and_cdms_communication_fails(auth_mock, live_server):
    """Test login valid cdms credentials when CDMS communication fails."""
    auth_mock.return_value = None

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
@mock.patch('datahub.core.auth.CDMSUserBackend.validate_cdms_credentials')
def test_password_changed_in_cdms(auth_mock, live_server):
    """Test passwd changed in CDMS results in failed auth."""
    auth_mock.return_value = False

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
@mock.patch('datahub.core.auth.CDMSUserBackend.validate_cdms_credentials')
def test_valid_cdms_credentials_user_not_whitelisted(auth_mock, live_server):
    """Test login valid cdms credentials, but user not whitelisted."""
    auth_mock.return_value = True
    cdms_user = get_cdms_user()
    cdms_user.use_cdms_auth = False
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
        data={
            'grant_type': 'password',
            'username': cdms_user.email,
            'password': cdms_user.password
        },
        auth=auth
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Invalid credentials given' in response.text


@pytest.mark.liveserver
@mock.patch('datahub.core.auth.CDMSUserBackend.validate_cdms_credentials')
def test_valid_django_user(auth_mock, live_server):
    """Test login valid Django credentials."""
    auth_mock.return_value = False
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
        data={
            'grant_type': 'password',
            'username': django_user.email,
            'password': DJANGO_USER_PASSWORD
        },
        auth=auth
    )
    assert response.status_code == status.HTTP_200_OK
    assert '"token_type": "Bearer"' in response.text


def test_submit_form():
    """Test successfully submitting cdms form."""
    response_mock = mock.Mock()
    response_mock.ok = True
    response_mock.content = '''
    <form action="foo">
    <input name="test1" value="test1_val" type="text">
    </form>
    '''
    session_mock = mock.Mock()
    session_mock.post.return_value = response_mock
    source = '''
    <form action="foo2">
    <input name="test2" value="test2_val" type="text">
    </form>
    '''

    resp = auth.CDMSUserBackend._submit_form(
        session_mock,
        source,
        params={'injected': 'param'},
    )

    assert resp is response_mock
    session_mock.post.assert_called_once_with(
        'foo2',
        dict(
            test2='test2_val',
            injected='param',
        ),
    )


def test_submit_form_unauthenticated():
    """Test successfully submitting cdms form but auth failed."""
    response_mock = mock.Mock()
    response_mock.ok = False
    session_mock = mock.Mock()
    session_mock.post.return_value = response_mock
    source = '''
    <form action="foo2">
    <input name="test2" value="test2_val" type="text">
    </form>
    '''

    with pytest.raises(auth.CDMSInvalidCredentialsError):
        auth.CDMSUserBackend._submit_form(
            session_mock,
            source,
            params={'injected': 'param'},
        )
