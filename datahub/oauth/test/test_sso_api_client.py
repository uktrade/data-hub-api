import pytest
from django.conf import settings
from requests.exceptions import ConnectionError
from rest_framework import status


from datahub.oauth.sso_api_client import introspect_token, SSORequestError


class TestIntrospectToken:
    """Tests for introspect_token()."""

    @pytest.mark.parametrize(
        'mock_kwargs,expected_exception_text',
        (
            (
                {'status_code': status.HTTP_400_BAD_REQUEST},
                'SSO request failed',
            ),
            (
                {'exc': ConnectionError},
                'SSO request failed',
            ),
            (
                {'text': '{"invalid-json}'},
                'SSO response parsing failed',
            ),
            # Valid JSON but expected properties missing
            (
                {'json': {}},
                'SSO response validation failed',
            ),
        ),
    )
    def test_error_handling(self, requests_mock, mock_kwargs, expected_exception_text):
        """Test that various errors are handled as expected."""
        requests_mock.post(
            f'{settings.STAFF_SSO_BASE_URL}o/introspect/',
            **mock_kwargs,
        )
        with pytest.raises(SSORequestError) as excinfo:
            introspect_token('test-token')

        assert str(excinfo.value) == expected_exception_text

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
