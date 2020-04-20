from datetime import datetime

import pytest
from django.contrib.auth import login as django_login
from django.urls import reverse
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status

from datahub.company.test.factories import AdviserFactory
from datahub.core.utils import reverse_with_query_string
from datahub.oauth.admin_sso.middleware import OAuthSessionMiddleware
from datahub.oauth.admin_sso.test.utils import get_request_with_session

pytestmark = pytest.mark.django_db


FROZEN_TIME = datetime(2018, 6, 1, 2, tzinfo=utc)


@freeze_time(FROZEN_TIME)
def test_user_is_logged_out_from_admin_when_oauth2_session_has_expired():
    """Tests that user is logged out if OAuth2 session is expired."""
    adviser = AdviserFactory()

    admin_url = reverse('admin:index')
    request = get_request_with_session(admin_url)
    request.session['oauth.expires_on'] = int(FROZEN_TIME.timestamp()) - 1
    django_login(request, adviser)

    assert request.user.is_authenticated

    oauth_session_middleware = OAuthSessionMiddleware(_get_response)
    response = oauth_session_middleware(request)

    assert not request.user.is_authenticated

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == reverse_with_query_string('admin:login', {'next': request.path})
    assert 'oauth.state' not in request.session


@freeze_time(FROZEN_TIME)
def test_user_is_not_logged_out_when_oauth2_session_is_not_expired():
    """
    Tests that user is not logged out if OAuth2 session is not expired.
    """
    adviser = AdviserFactory()

    admin_url = reverse('admin:index')
    request = get_request_with_session(admin_url)
    request.session['oauth.expires_on'] = int(FROZEN_TIME.timestamp()) + 1

    django_login(request, adviser)

    assert request.user.is_authenticated

    oauth_session_middleware = OAuthSessionMiddleware(_get_response)
    oauth_session_middleware(request)

    assert request.user.is_authenticated


def _get_response(response):
    return response
