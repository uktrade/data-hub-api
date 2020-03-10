from secrets import token_urlsafe
from unittest.mock import patch
from urllib.parse import urlencode, urljoin

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from datahub.company.test.factories import AdviserFactory
from datahub.oauth.admin.test.utils import (
    extract_next_url_from_redirect_url,
    extract_next_url_from_url,
    get_request_with_session,
)
from datahub.oauth.admin.views import callback, login, logout

pytestmark = pytest.mark.django_db


@patch('datahub.oauth.admin.views.token_urlsafe')
def test_login_view_redirects_to_sso_auth_url(_token_urlsafe):
    """Tests that login view redirects to Staff SSO Auth URL."""
    _token_urlsafe.return_value = 'aZFsiJfbDLF9bwve8f2HTBeC1rCnhFUn4K6c_iq-wLo'

    request = get_request_with_session(reverse('admin:login'))
    response = login(request)

    oauth_url_params = {
        'response_type': 'code',
        'client_id': settings.ADMIN_OAUTH2_CLIENT_ID,
        'redirect_uri': request.build_absolute_uri(reverse('admin_oauth_callback')),
        'state': _token_urlsafe.return_value,
        'idp': 'cirrus',
    }

    redirect_url = urljoin(settings.ADMIN_OAUTH2_BASE_URL, settings.ADMIN_OAUTH2_AUTH_PATH)
    expected_url = f'{redirect_url}?{urlencode(oauth_url_params)}'

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == expected_url
    assert request.session['oauth.state'] == _token_urlsafe.return_value


def test_login_view_redirects_with_next_url():
    """Tests that login view redirects to Staff SSO with next URL."""
    login_url = reverse('admin:login')
    request = get_request_with_session(f'{login_url}?next=/protected-area')
    response = login(request)

    assert response.status_code == status.HTTP_302_FOUND

    next_url = extract_next_url_from_redirect_url(response.url)
    assert next_url == '/protected-area'


@pytest.mark.parametrize(
    'dangerous_redirect',
    (
        'https://external-dangerous-website/protected-area',
        'javascript:alert("Meow!")',
    ),
)
def test_login_view_validates_next_url(dangerous_redirect):
    """Tests that login view checks redirect URLs for safety."""
    login_url = reverse('admin:login')
    request = get_request_with_session(
        f'{login_url}?next={dangerous_redirect}',
    )
    response = login(request)

    assert response.status_code == status.HTTP_302_FOUND
    assert extract_next_url_from_redirect_url(response.url) is None


def test_logout():
    """Test that logout view clears session data and redirects to SSO Logout URL."""
    request = get_request_with_session(reverse('admin:logout'))

    fake_state_id = token_urlsafe(settings.ADMIN_OAUTH2_TOKEN_BYTE_LENGTH)
    request.session['oauth.state'] = fake_state_id

    response = logout(request)
    assert response.status_code == status.HTTP_302_FOUND

    expected_path = urljoin(settings.ADMIN_OAUTH2_BASE_URL, settings.ADMIN_OAUTH2_LOGOUT_PATH)
    assert response.url == expected_path

    assert 'oauth.state' not in request.session
    assert not request.user.is_authenticated


def test_callback_without_state():
    """Test that a callback without provided state will restart login process."""
    request = get_request_with_session('/oauth/callback')

    response = callback(request)

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == request.build_absolute_uri(reverse('admin:login'))


def test_callback_without_state_includes_next_url():
    """
    Test that a callback without provided state will restart login process including next URL.
    """
    request = get_request_with_session('/oauth/callback/?next=/protected-area')

    response = callback(request)

    assert response.status_code == status.HTTP_302_FOUND
    next_url = extract_next_url_from_url(response.url)
    assert next_url == '/protected-area'


def test_callback_with_state_mismatch():
    """Test that a callback without matching state will return an error page."""
    fake_state_id = token_urlsafe(settings.ADMIN_OAUTH2_TOKEN_BYTE_LENGTH)

    request = get_request_with_session('/oauth/callback/?state=wrong-one')
    request.session['oauth.state'] = fake_state_id
    response = callback(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN

    response.render()
    response_content = str(response.content)
    assert 'State mismatch.' in response_content
    assert not request.user.is_authenticated


def test_callback_without_access_code():
    """Test that a callback without a code will return an error page."""
    fake_state_id = token_urlsafe(settings.ADMIN_OAUTH2_TOKEN_BYTE_LENGTH)

    request = get_request_with_session(f'/oauth/callback/?state={fake_state_id}')
    request.session['oauth.state'] = fake_state_id
    response = callback(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN

    response.render()
    response_content = str(response.content)
    assert 'Forbidden.' in response_content
    assert not request.user.is_authenticated


@patch('datahub.oauth.admin.views.get_access_token')
@patch('datahub.oauth.admin.views.get_sso_user_profile')
def test_callback_requests_sso_profile_no_user(get_sso_user_profile, get_access_token):
    """Test that if SSO user is not found then no access is granted."""
    get_access_token.return_value = {'access_token': 'access-token', 'expires_in': 3600}
    get_sso_user_profile.return_value = {'email': 'some@email'}

    fake_state_id = token_urlsafe(settings.ADMIN_OAUTH2_TOKEN_BYTE_LENGTH)

    request = get_request_with_session(f'/oauth/callback/?state={fake_state_id}&code=code')
    request.session['oauth.state'] = fake_state_id
    response = callback(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN

    response.render()
    response_content = str(response.content)
    assert 'Forbidden.' in response_content
    assert not request.user.is_authenticated


@patch('datahub.oauth.admin.views.get_access_token')
@patch('datahub.oauth.admin.views.get_sso_user_profile')
@pytest.mark.parametrize(
    'flags',
    (
        {'is_staff': False, 'is_active': True},
        {'is_staff': True, 'is_active': False},
        {'is_staff': False, 'is_active': False},
    ),
)
def test_callback_requests_sso_profile_valid_non_staff_user_by_email(
    get_sso_user_profile,
    get_access_token,
    flags,
    caplog,
):
    """
    Test that if SSO user has a matching email, but Data Hub user has `is_staff` or `is_active`
    flag not set, then the access is forbidden.
    """
    AdviserFactory(email='some@email', **flags)

    get_access_token.return_value = {'access_token': 'access-token'}
    get_sso_user_profile.return_value = {'email': 'some@email'}

    request = get_request_with_session('/oauth/callback/?state=original&code=code')
    request.session['oauth.state'] = 'original'
    response = callback(request)
    response.render()

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'Forbidden.' in str(response.content)
    assert not request.user.is_authenticated
    assert len(caplog.records) == 1
    assert 'Django Admin OAuth2 authentication failed: User not found.' in caplog.text


@pytest.mark.usefixtures('local_memory_cache')
@patch('datahub.oauth.admin.views.get_access_token')
@patch('datahub.oauth.admin.views.get_sso_user_profile')
def test_callback_requests_sso_profile_valid_email(get_sso_user_profile, get_access_token):
    """
    Test that if SSO user has a matching email (and relevant flags), then the access is granted.
    """
    fake_state_id = token_urlsafe(settings.ADMIN_OAUTH2_TOKEN_BYTE_LENGTH)
    adviser = AdviserFactory(email='some@email', is_staff=True, is_active=True)

    get_access_token.return_value = {'access_token': 'access-token', 'expires_in': 3600}
    get_sso_user_profile.return_value = {'email': 'some@email'}

    request = get_request_with_session(f'/oauth/callback/?state={fake_state_id}&code=code')

    request.session['oauth.state'] = fake_state_id

    response = callback(request)

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == reverse('admin:index')
    assert request.user.is_authenticated
    assert request.user == adviser


@patch('datahub.oauth.admin.views.get_access_token')
@patch('datahub.oauth.admin.views.get_sso_user_profile')
def test_callback_redirects_to_next_url(get_sso_user_profile, get_access_token):
    """Test that successful login redirects user to `next_url`."""
    fake_state_id = token_urlsafe(settings.ADMIN_OAUTH2_TOKEN_BYTE_LENGTH)
    AdviserFactory(email='some@email', is_staff=True, is_active=True)

    get_access_token.return_value = {'access_token': 'access-token', 'expires_in': 3600}
    get_sso_user_profile.return_value = {'email': 'some@email'}

    request = get_request_with_session(
        f'/oauth/callback/?next=/some-location&state={fake_state_id}&code=code',
    )
    request.session['oauth.state'] = fake_state_id

    response = callback(request)

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == '/some-location'


@pytest.mark.usefixtures('local_memory_cache')
@patch('datahub.oauth.admin.views.get_access_token')
@patch('datahub.oauth.admin.views.get_sso_user_profile')
@pytest.mark.parametrize(
    'dangerous_redirect',
    (
        'https://external-dangerous-website/protected-area',
        'javascript:alert("Meow!")',
    ),
)
def test_callback_validates_next_url(get_sso_user_profile, get_access_token, dangerous_redirect):
    """Test that successful login redirects user to `next_url`."""
    fake_state_id = token_urlsafe(settings.ADMIN_OAUTH2_TOKEN_BYTE_LENGTH)
    AdviserFactory(email='some@email', is_staff=True, is_active=True)

    get_access_token.return_value = {'access_token': 'access-token', 'expires_in': 3600}
    get_sso_user_profile.return_value = {'email': 'some@email'}

    request = get_request_with_session(
        f'/oauth/callback/?next={dangerous_redirect}&state={fake_state_id}&code=code',
    )
    request.session['oauth.state'] = fake_state_id

    response = callback(request)

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == reverse('admin:index')
