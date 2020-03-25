from urllib.parse import urlencode

import pytest
from django.conf import settings
from requests.exceptions import ConnectionError
from rest_framework import status


from datahub.oauth.sso_api_client import (
    get_user_by_email,
    get_user_by_email_user_id,
    introspect_token,
    SSORequestError,
    SSOTokenDoesNotExist,
    SSOUserDoesNotExist,
)


FAKE_SSO_USER_DATA = {
    'email': 'email@email.test',
    'user_id': 'c2c1afce-e45e-4139-9913-88b350f7a546',
    'email_user_id': 'test@id.test',
    'first_name': 'Johnny',
    'last_name': 'Cakeman',
    'related_emails': ['related@email.test'],
    'contact_email': 'contact@email.test',
    'groups': [],
    'permitted_applications': [
        {
            'key': 'an-app',
            'url': 'https://app.invalid',
            'name': 'An app',
        },
    ],
    'access_profiles': ['an-access-profile'],
}


class TestIntrospectToken:
    """Tests for introspect_token()."""

    @pytest.mark.parametrize(
        'mock_kwargs,expected_exception',
        (
            (
                {'status_code': status.HTTP_400_BAD_REQUEST},
                SSORequestError('SSO request failed'),
            ),
            (
                {
                    'status_code': status.HTTP_401_UNAUTHORIZED,
                    'json': {'active': False},
                },
                SSOTokenDoesNotExist(),
            ),
            (
                {'exc': ConnectionError},
                SSORequestError('SSO request failed'),
            ),
            (
                {'text': '{"invalid-json}'},
                SSORequestError('SSO response parsing failed'),
            ),
            # Valid JSON but expected properties missing
            (
                {'json': {}},
                SSORequestError('SSO response validation failed'),
            ),
        ),
    )
    def test_error_handling(self, requests_mock, mock_kwargs, expected_exception):
        """Test that various errors are handled as expected."""
        requests_mock.post(
            f'{settings.STAFF_SSO_BASE_URL}o/introspect/',
            **mock_kwargs,
        )
        with pytest.raises(expected_exception.__class__) as excinfo:
            introspect_token('test-token')

        assert str(excinfo.value) == str(expected_exception)

    def test_returns_validated_data(self, requests_mock):
        """Test that introspected token data is returned on success."""
        mock_data = {
            'active': True,
            'username': 'username@example.test',
            'email_user_id': 'user_id@example.test',
            'exp': 1584118925,
        }
        requests_mock.post(
            f'{settings.STAFF_SSO_BASE_URL}o/introspect/',
            json=mock_data,
        )
        assert introspect_token('test-token') == mock_data
        assert requests_mock.last_request.text == 'token=test-token'


class TestGetUserByEmail:
    """Tests for get_user_by_email()."""

    @pytest.mark.parametrize(
        'mock_kwargs,expected_exception',
        (
            (
                {'status_code': status.HTTP_400_BAD_REQUEST},
                SSORequestError('SSO request failed'),
            ),
            (
                {'status_code': status.HTTP_404_NOT_FOUND},
                SSOUserDoesNotExist(),
            ),
            (
                {'exc': ConnectionError},
                SSORequestError('SSO request failed'),
            ),
            (
                {'text': '{"invalid-json}'},
                SSORequestError('SSO response parsing failed'),
            ),
        ),
    )
    def test_error_handling(self, requests_mock, mock_kwargs, expected_exception):
        """Test that various errors are handled as expected."""
        params = {'email': 'email@email.test'}
        request_url = f'{settings.STAFF_SSO_BASE_URL}api/v1/user/introspect/?{urlencode(params)}'
        requests_mock.get(request_url, **mock_kwargs)

        with pytest.raises(expected_exception.__class__) as excinfo:
            get_user_by_email('email@email.test')

        assert str(excinfo.value) == str(expected_exception)

    def test_returns_data_on_success(self, requests_mock):
        """Test that user data is returned on success."""
        params = {'email': 'email@email.test'}
        request_url = f'{settings.STAFF_SSO_BASE_URL}api/v1/user/introspect/?{urlencode(params)}'
        requests_mock.get(request_url, json=FAKE_SSO_USER_DATA)

        assert get_user_by_email('email@email.test') == FAKE_SSO_USER_DATA


class TestGetUserByEmailUserID:
    """Tests for get_user_by_email_user_id()."""

    @pytest.mark.parametrize(
        'mock_kwargs,expected_exception',
        (
            (
                {'status_code': status.HTTP_400_BAD_REQUEST},
                SSORequestError('SSO request failed'),
            ),
            (
                {'status_code': status.HTTP_404_NOT_FOUND},
                SSOUserDoesNotExist(),
            ),
            (
                {'exc': ConnectionError},
                SSORequestError('SSO request failed'),
            ),
            (
                {'text': '{"invalid-json}'},
                SSORequestError('SSO response parsing failed'),
            ),
        ),
    )
    def test_error_handling(self, requests_mock, mock_kwargs, expected_exception):
        """Test that various errors are handled as expected."""
        params = {'email_user_id': 'test@id.test'}
        request_url = f'{settings.STAFF_SSO_BASE_URL}api/v1/user/introspect/?{urlencode(params)}'
        requests_mock.get(request_url, **mock_kwargs)

        with pytest.raises(expected_exception.__class__) as excinfo:
            get_user_by_email_user_id('test@id.test')

        assert str(excinfo.value) == str(expected_exception)

    def test_returns_data_on_success(self, requests_mock):
        """Test that user data is returned on success."""
        params = {'email_user_id': 'test@id.test'}
        request_url = f'{settings.STAFF_SSO_BASE_URL}api/v1/user/introspect/?{urlencode(params)}'
        requests_mock.get(request_url, json=FAKE_SSO_USER_DATA)

        assert get_user_by_email_user_id('test@id.test') == FAKE_SSO_USER_DATA
