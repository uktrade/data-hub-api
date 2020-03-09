from base64 import b64encode
from unittest import mock
from urllib.parse import urlencode

import pytest
from django.utils.timezone import utc
from factory import Faker
from oauth2_provider.models import Application
from rest_framework import HTTP_HEADER_ENCODING, status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.core.test_utils import APITestMixin
from datahub.oauth.scopes import SCOPES_DESCS
from datahub.oauth.test.factories import AccessTokenFactory, OAuthApplicationScopeFactory
from datahub.oauth.test.scopes import TEST_SCOPES_DESC, TestScope

pytestmark = pytest.mark.django_db


@mock.patch.dict(SCOPES_DESCS, TEST_SCOPES_DESC)
class TestOAuthScopeBackend:
    """Tests app-specific OAuth scopes."""

    def test_creating_a_token_default_scope(self):
        """Test creating an access token with default application scopes."""
        app_and_scope = OAuthApplicationScopeFactory(scopes=[TestScope.test_scope_1])
        app = app_and_scope.application
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=_create_auth_header(app.client_id, app.client_secret),
        )
        data = {'grant_type': 'client_credentials'}
        url = reverse('token')
        response = client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['scope'] == TestScope.test_scope_1

    def test_creating_a_token_allowed_scope(self):
        """Test creating an access token with specified application scopes."""
        app_and_scope = OAuthApplicationScopeFactory(scopes=[
            TestScope.test_scope_1,
            TestScope.test_scope_2,
        ])
        app = app_and_scope.application
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=_create_auth_header(app.client_id, app.client_secret),
        )
        data = {
            'grant_type': 'client_credentials',
            'scope': TestScope.test_scope_1.value,
        }
        url = reverse('token')
        response = client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['scope'] == TestScope.test_scope_1.value

    def test_creating_a_token_disallowed_scope(self):
        """
        Test creating an access token when specifying a scope that the app hasn't been assigned.
        """
        app_and_scope = OAuthApplicationScopeFactory(scopes=[
            TestScope.test_scope_1,
        ])
        app = app_and_scope.application
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=_create_auth_header(app.client_id, app.client_secret),
        )
        data = {
            'grant_type': 'client_credentials',
            'scope': TestScope.test_scope_2.value,
        }
        url = reverse('token')
        response = client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'error': 'invalid_scope',
        }


@mock.patch.dict(SCOPES_DESCS, TEST_SCOPES_DESC)
@pytest.mark.urls('datahub.core.test.support.urls')
class TestOAuthViewScope(APITestMixin):
    """Tests app-specific OAuth scopes in views."""

    @pytest.mark.parametrize(
        'grant_type',
        (
            Application.GRANT_PASSWORD,
            Application.GRANT_CLIENT_CREDENTIALS,
        ),
    )
    def test_scope_allowed(self, grant_type):
        """Tests a test view with the required scope."""
        client = self.create_api_client(TestScope.test_scope_1, grant_type=grant_type)
        url = reverse('test-disableable-collection')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        'grant_type',
        (
            Application.GRANT_PASSWORD,
            Application.GRANT_CLIENT_CREDENTIALS,
        ),
    )
    def test_scope_not_allowed(self, grant_type):
        """Tests a test view without the required scope."""
        client = self.create_api_client(TestScope.test_scope_2, grant_type=grant_type)
        url = reverse('test-disableable-collection')
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'grant_type',
        (
            Application.GRANT_PASSWORD,
            Application.GRANT_CLIENT_CREDENTIALS,
        ),
    )
    def test_expired_token(self, grant_type):
        """Tests a test view with an expired token and the required scope."""
        application = self.get_application(grant_type=grant_type)
        access_token = AccessTokenFactory(
            application=application,
            scope=TestScope.test_scope_1,
            expires=Faker('past_datetime', tzinfo=utc),
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'bearer {access_token.token}')
        url = reverse('test-disableable-collection')
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated(self):
        """Tests a test view unauthenticated."""
        client = APIClient()
        url = reverse('test-disableable-collection')
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def _create_auth_header(user, password):
    """Constructs an auth header for basic auth."""
    base64_credentials = b64encode(f'{user}:{password}'.encode(HTTP_HEADER_ENCODING))
    base64_credentials_as_string = base64_credentials.decode(HTTP_HEADER_ENCODING)
    return f'Basic {base64_credentials_as_string}'
