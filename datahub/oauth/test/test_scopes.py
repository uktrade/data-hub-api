from base64 import b64encode

import pytest
from rest_framework import HTTP_HEADER_ENCODING, status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.oauth.test.factories import OAuthApplicationScopeFactory


pytestmark = pytest.mark.django_db


class TestOAuth:
    """Tests app-specific OAuth scopes."""

    def test_creating_a_token_default_scope(self):
        """Test creating an access token with default application scopes."""
        app_and_scope = OAuthApplicationScopeFactory(scopes=['test_scope_1'])
        app = app_and_scope.application
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=_create_auth_header(app.client_id, app.client_secret)
        )
        url = reverse('token')
        response = client.post(url, data={
            'grant_type': 'client_credentials',
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['scope'] == 'test_scope_1'

    def test_creating_a_token_allowed_scope(self):
        """Test creating an access token with specified application scopes."""
        app_and_scope = OAuthApplicationScopeFactory(scopes=['test_scope_1', 'test_scope_2'])
        app = app_and_scope.application
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=_create_auth_header(app.client_id, app.client_secret)
        )
        url = reverse('token')
        response = client.post(url, data={
            'grant_type': 'client_credentials',
            'scope': 'test_scope_1',
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['scope'] == 'test_scope_1'

    def test_creating_a_token_disallowed_scope(self):
        """
        Test creating an access token when specifying a scope that the app hasn't been assigned.
        """
        app_and_scope = OAuthApplicationScopeFactory(scopes=['test_scope_1'])
        app = app_and_scope.application
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=_create_auth_header(app.client_id, app.client_secret)
        )
        url = reverse('token')
        response = client.post(url, data={
            'grant_type': 'client_credentials',
            'scope': 'test_scope_2',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            'error': 'invalid_scope'
        }


def _create_auth_header(user, password):
    """Constructs an auth header for basic auth."""
    base64_credentials = b64encode(f'{user}:{password}'.encode(HTTP_HEADER_ENCODING))
    base64_credentials_as_string = base64_credentials.decode(HTTP_HEADER_ENCODING)
    return f'Basic {base64_credentials_as_string}'
