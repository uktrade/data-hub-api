from urllib.parse import urlencode

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed

from datahub.company.test.factories import AdviserFactory
from datahub.oauth.admin.test.utils import (
    get_request_with_session,
)
from datahub.oauth.admin.utils import (
    get_access_token,
    get_adviser_by_sso_user_profile,
    get_sso_user_profile,
)

pytestmark = pytest.mark.django_db


def test_get_access_token(requests_mock):
    """Test that access token is being requested."""
    token_data = {'access_token': 'example-token'}

    requests_mock.post(
        settings.ADMIN_OAUTH2_TOKEN_FETCH_PATH,
        status_code=status.HTTP_200_OK,
        json=token_data,
    )

    request = get_request_with_session(reverse('admin:index'))
    access_token_data = get_access_token(
        '1234',
        request.build_absolute_uri(reverse('admin_oauth_callback')),
    )

    oauth_params = {
        'code': '1234',
        'grant_type': 'authorization_code',
        'client_id': settings.ADMIN_OAUTH2_CLIENT_ID,
        'client_secret': settings.ADMIN_OAUTH2_CLIENT_SECRET,
        'redirect_uri': request.build_absolute_uri(reverse('admin_oauth_callback')),
    }

    assert requests_mock.call_count == 1
    expected_url = f'{settings.ADMIN_OAUTH2_TOKEN_FETCH_PATH}?{urlencode(oauth_params)}'
    assert requests_mock.request_history[-1].url == expected_url

    assert access_token_data == token_data


def test_get_access_token_error(requests_mock):
    """Test that AuthenticationFailed is raised on error."""
    requests_mock.post(
        settings.ADMIN_OAUTH2_TOKEN_FETCH_PATH,
        status_code=status.HTTP_200_OK,
        json={'error': 'Too many cats.'},
    )

    request = get_request_with_session(reverse('admin:index'))

    with pytest.raises(AuthenticationFailed) as excinfo:
        get_access_token(
            '1234',
            request.build_absolute_uri(reverse('admin_oauth_callback')),
        )

    assert excinfo.value.detail == 'Too many cats.'


def test_get_access_token_missing(requests_mock):
    """Test that AuthenticationFailed is raised on missing token."""
    requests_mock.post(
        settings.ADMIN_OAUTH2_TOKEN_FETCH_PATH,
        status_code=status.HTTP_200_OK,
        json={},
    )

    request = get_request_with_session(reverse('admin:index'))

    with pytest.raises(AuthenticationFailed) as excinfo:
        get_access_token(
            '1234',
            request.build_absolute_uri(reverse('admin_oauth_callback')),
        )

    assert excinfo.value.detail == 'No access token.'


def test_get_sso_user_profile(requests_mock):
    """Tests that SSO user profile is being requested."""
    requests_mock.get(
        settings.ADMIN_OAUTH2_USER_PROFILE_PATH,
        status_code=status.HTTP_200_OK,
        json={'email': 'what@email', 'email_user_id': 'what-123@email'},
    )

    sso_user_profile = get_sso_user_profile('1234')

    assert requests_mock.call_count == 1
    assert requests_mock.request_history[-1].url == settings.ADMIN_OAUTH2_USER_PROFILE_PATH

    assert sso_user_profile == {'email': 'what@email', 'email_user_id': 'what-123@email'}


def test_get_sso_user_profile_error(requests_mock):
    """Test that AuthenticationFailed exception is raised when SSO user profile is not received."""
    requests_mock.get(
        settings.ADMIN_OAUTH2_USER_PROFILE_PATH,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    with pytest.raises(AuthenticationFailed) as excinfo:
        get_sso_user_profile('1234')

    assert excinfo.value.detail == 'Cannot get user profile.'


def test_get_adviser_by_sso_user_profile_no_staff_email_id():
    """Test that AuthenticationFailed is raised if staff SSO email user id doesn't match."""
    AdviserFactory(is_staff=True, is_active=True)

    with pytest.raises(AuthenticationFailed) as excinfo:
        get_adviser_by_sso_user_profile({'email_user_id': 'some-123@email'})
    assert excinfo.value.detail == 'User not found.'


def test_get_adviser_by_sso_user_profile_email_id():
    """Test that adviser is returned if staff SSO email user id matches."""
    adviser = AdviserFactory(sso_email_user_id='some-123@email', is_staff=True, is_active=True)
    sso_adviser = get_adviser_by_sso_user_profile({'email_user_id': 'some-123@email'})

    assert sso_adviser.pk == adviser.pk
    assert sso_adviser.sso_email_user_id == 'some-123@email'


@pytest.mark.parametrize(
    'flags',
    (
        {'is_staff': False, 'is_active': True},
        {'is_staff': True, 'is_active': False},
        {'is_staff': False, 'is_active': False},
    ),
)
def test_get_adviser_by_sso_email_id_non_staff_or_active(flags):
    """
    Test that AuthenticationFailed is raised if SSO email user id matches and user has neither
    is_staff nor is_active flags set.
    """
    AdviserFactory(sso_email_user_id='some-123@email', **flags)
    with pytest.raises(AuthenticationFailed) as excinfo:
        get_adviser_by_sso_user_profile({'email_user_id': 'some-123@email'})

    assert excinfo.value.detail == 'User not found.'
