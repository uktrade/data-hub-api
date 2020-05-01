from datetime import timedelta
from unittest.mock import patch
from urllib.parse import urlencode

import pytest
from django.conf import settings
from django.utils.timezone import now
from oauth2_provider.admin import AccessToken
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.core.viewsets import CoreViewSet


@pytest.fixture
def oauth2_backend_class(monkeypatch):
    """Ensure ContentTypeAwareOAuthLibCore is being set."""
    monkeypatch.setitem(
        settings.OAUTH2_PROVIDER,
        'OAUTH2_BACKEND_CLASS',
        'datahub.oauth.backend.ContentTypeAwareOAuthLibCore',
    )


class RestrictedAccessViewSet(CoreViewSet):
    """DRF ViewSet to test authentication."""

    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)


class TestContentTypeAwareOAuthLibCore(APITestMixin):
    """Tests for ContentTypeAwareOAuthLibCore."""

    @pytest.mark.parametrize(
        'token',
        (
            'Bearer token',
            '',
            'Cool cats',
        ),
    )
    @patch.object(RestrictedAccessViewSet, 'create')
    def test_request_is_not_parsed_if_oauth2_token_is_invalid_and_content_type_is_application_json(
        self,
        create,
        token,
        oauth2_backend_class,
        api_request_factory,
    ):
        """
        Tests that if the oauth2 token is invalid and contenty type is application.json,
        the request is not being parsed.
        """
        request = api_request_factory.post(
            '/',
            # sending invalid JSON
            data=b'{"what": "cat}',
            content_type='application/json',
            HTTP_AUTHORIZATION=token,
        )
        my_view = RestrictedAccessViewSet.as_view(
            actions={'post': 'create'},
        )
        response = my_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        create.assert_not_called()

    @pytest.mark.parametrize(
        'content_type,expected_authorized',
        (
            ('application/x-www-form-urlencoded; charset=utf-8', True),
            ('application/x-www-form-urlencoded;', True),
            ('application/cats-on-mars', False),
        ),
    )
    @patch.object(RestrictedAccessViewSet, 'create')
    def test_request_is_parsed_if_oauth2_token_is_in_the_form(
        self,
        create,
        content_type,
        expected_authorized,
        oauth2_backend_class,
        api_request_factory,
    ):
        """Tests that the request is being parsed if the auth token is in the form."""
        if expected_authorized:
            create.return_value = Response(data={'result': True})

        user = create_test_user()
        access_token = AccessToken.objects.create(
            token='test-token',
            expires=now() + timedelta(days=365),
            user=user,
        )
        data = {
            'access_token': access_token.token,
        }
        request = api_request_factory.post(
            '/',
            data=urlencode(data),
            content_type=content_type,
        )
        my_view = RestrictedAccessViewSet.as_view(
            actions={'post': 'create'},
        )
        response = my_view(request)
        if expected_authorized:
            assert response.status_code == status.HTTP_200_OK
            create.assert_called_once()
        else:
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            create.assert_not_called()
