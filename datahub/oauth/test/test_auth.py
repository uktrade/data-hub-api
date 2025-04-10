from datetime import datetime, timedelta, timezone

import pytest
from django.conf import settings
from django.core.cache import cache
from freezegun import freeze_time
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.company.test.factories import AdviserFactory
from datahub.oauth.auth import SSOIntrospectionAuthentication
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.models import UserEvent

FROZEN_DATETIME = datetime(2020, 1, 1, 0, tzinfo=timezone.utc)
STAFF_SSO_INTROSPECT_URL = f'{settings.STAFF_SSO_BASE_URL}o/introspect/'
EXAMPLE_SSO_EMAIL_USER_ID = 'user_id@example.test'


class IntrospectionAuthView(APIView):
    """View using SSOIntrospectionAuthentication."""

    authentication_classes = (SSOIntrospectionAuthentication,)
    permission_classes = ()

    def get(self, request):
        """Simple test view with fixed response."""
        return Response({'content': 'introspection-test-view'})


view = IntrospectionAuthView.as_view()


def _make_introspection_data(**overrides):
    return {
        'active': True,
        'username': 'email@example.test',
        'email_user_id': EXAMPLE_SSO_EMAIL_USER_ID,
        'exp': (FROZEN_DATETIME + timedelta(hours=10)).timestamp(),
        **overrides,
    }


@pytest.mark.django_db
@pytest.mark.usefixtures('local_memory_cache')
@freeze_time(FROZEN_DATETIME)
class TestSSOIntrospectionAuthentication:
    """Tests for SSOIntrospectionAuthentication."""

    @pytest.mark.parametrize(
        ('request_kwargs', 'expected_error'),
        [
            pytest.param(
                {},
                'Authentication credentials were not provided.',
                id='no-header',
            ),
            pytest.param(
                {'HTTP_AUTHORIZATION': 'wrong-scheme-no-space'},
                'Incorrect authentication scheme.',
                id='wrong-scheme-no-space',
            ),
            pytest.param(
                {'HTTP_AUTHORIZATION': 'wrong-scheme 8jol80DF'},
                'Incorrect authentication scheme.',
                id='wrong-scheme',
            ),
            pytest.param(
                {'HTTP_AUTHORIZATION': 'bearer'},
                'Authentication credentials were not provided.',
                id='no-token',
            ),
        ],
    )
    def test_rejects_malformed_headers(
        self,
        api_request_factory,
        request_kwargs,
        expected_error,
    ):
        """Test that errors are returned for various header values."""
        request = api_request_factory.get('/test-path', **request_kwargs)
        response = view(request)

        assert response['WWW-Authenticate'] == 'Bearer realm="api"'
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {'detail': expected_error}
        assert not request.user

    @pytest.mark.parametrize(
        'response_kwargs',
        [
            pytest.param(
                {
                    'status_code': status.HTTP_401_UNAUTHORIZED,
                    'json': {'active': False},
                },
                id='non-existent-token',
            ),
            pytest.param(
                {
                    'status_code': status.HTTP_200_OK,
                    'json': {},
                },
                id='inactive-response',
            ),
            pytest.param(
                {
                    'status_code': status.HTTP_200_OK,
                    'json': {'active': False},
                },
                id='expired-token',
            ),
            # Should not happen in reality
            pytest.param(
                {
                    'status_code': status.HTTP_200_OK,
                    'json': _make_introspection_data(exp=FROZEN_DATETIME.timestamp() - 1),
                },
                id='expired-token',
            ),
        ],
    )
    def test_authentication_fails_on_introspection_failure(
        self,
        response_kwargs,
        api_request_factory,
        requests_mock,
    ):
        """Test that authentication fails and an error is returned when introspection fails."""
        AdviserFactory(sso_email_user_id='user_id@example.test')
        requests_mock.post(STAFF_SSO_INTROSPECT_URL, **response_kwargs)

        request = api_request_factory.get('/test-path', HTTP_AUTHORIZATION='Bearer token')
        response = view(request)
        assert not request.user
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {'detail': 'Invalid authentication credentials.'}

    def test_authenticates_if_noncached_token_provided(self, api_request_factory, requests_mock):
        """Test that authentication is successful if a valid, non-cached token is provided."""
        adviser = AdviserFactory(sso_email_user_id=EXAMPLE_SSO_EMAIL_USER_ID)
        requests_mock.post(STAFF_SSO_INTROSPECT_URL, json=_make_introspection_data())

        request = api_request_factory.get('/test-path', HTTP_AUTHORIZATION='Bearer token')
        response = view(request)
        assert request.user == adviser
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'content': 'introspection-test-view'}

        user_events = list(UserEvent.objects.all())
        assert len(user_events) == 1
        user_event = user_events[0]
        assert user_event.adviser == adviser
        assert user_event.type == UserEventType.OAUTH_TOKEN_INTROSPECTION
        assert user_event.api_url_path == '/test-path'

    def test_authenticates_if_token_is_cached(self, api_request_factory, requests_mock):
        """Test that authentication is successful if a valid, cached token is provided."""
        adviser = AdviserFactory(sso_email_user_id=EXAMPLE_SSO_EMAIL_USER_ID)
        cached_data = {
            'email': 'email@example.test',
            'sso_email_user_id': EXAMPLE_SSO_EMAIL_USER_ID,
        }
        cache.set('access_token:token', cached_data)

        request = api_request_factory.get('/test-path', HTTP_AUTHORIZATION='Bearer token')
        response = view(request)
        assert not requests_mock.called
        assert request.user == adviser
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'content': 'introspection-test-view'}

        assert not UserEvent.objects.exists()

    def test_caches_token_with_timeout_on_introspection(self, api_request_factory, requests_mock):
        """Test that after introspection, token data is cached with a timeout."""
        AdviserFactory(sso_email_user_id=EXAMPLE_SSO_EMAIL_USER_ID)
        introspection_data = _make_introspection_data()
        requests_mock.post(STAFF_SSO_INTROSPECT_URL, json=introspection_data)

        request = api_request_factory.get('/test-path', HTTP_AUTHORIZATION='Bearer token')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

        # Check that the returned token data is cached
        assert cache.get('access_token:token') == {
            'email': introspection_data['username'],
            'sso_email_user_id': introspection_data['email_user_id'],
        }

        caching_period = settings.STAFF_SSO_USER_TOKEN_CACHING_PERIOD
        post_expiry_time = FROZEN_DATETIME + timedelta(seconds=caching_period)

        # Check that the cached token data expires after the caching period
        with freeze_time(post_expiry_time):
            assert not cache.get('access_token:token')

    def test_authentication_fails_if_user_is_inactive(self, api_request_factory, requests_mock):
        """Test that authentication fails when there is a matching but inactive user."""
        AdviserFactory(sso_email_user_id=EXAMPLE_SSO_EMAIL_USER_ID, is_active=False)
        requests_mock.post(STAFF_SSO_INTROSPECT_URL, json=_make_introspection_data())

        request = api_request_factory.get('/test-path', HTTP_AUTHORIZATION='Bearer token')
        response = view(request)

        assert not request.user
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {'detail': 'Invalid authentication credentials.'}

    def test_authentication_fails_if_no_matching_user(self, api_request_factory, requests_mock):
        """Test that authentication fails when there is no matching adviser in Data Hub."""
        # Create an unrelated user that should not be returned
        AdviserFactory(email='unrelated@email.test', sso_email_user_id='unrelated@id.test')
        requests_mock.post(
            STAFF_SSO_INTROSPECT_URL,
            json=_make_introspection_data(username='email@email.test'),
        )

        request = api_request_factory.get('/test-path', HTTP_AUTHORIZATION='Bearer token')
        response = view(request)

        assert not request.user
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {'detail': 'Invalid authentication credentials.'}
