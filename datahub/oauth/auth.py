import time
from logging import getLogger
from typing import Optional, Tuple

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from datahub.company.models import Advisor
from datahub.oauth.cache import add_token_data_to_cache, get_token_data_from_cache
from datahub.oauth.sso_api_client import (
    SSOInvalidTokenError,
    SSORequestError,
    introspect_token,
)
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.utils import record_user_event

NO_CREDENTIALS_MESSAGE = 'Authentication credentials were not provided.'
INCORRECT_CREDENTIALS_MESSAGE = 'Incorrect authentication credentials.'
INCORRECT_SCHEME = 'Incorrect authentication scheme.'
INVALID_CREDENTIALS_MESSAGE = 'Invalid authentication credentials.'


logger = getLogger(__name__)


class SSOIntrospectionAuthentication(BaseAuthentication):
    """OAuth token introspection (RFC 7662) authentication class, with Staff SSO extensions."""

    def authenticate_header(self, request):
        """The value for the WWW-Authenticate for when credentials aren't provided.

        This returns the same value as django-oauth-toolkit.
        """
        return 'Bearer realm="api"'

    def authenticate(self, request):
        """Authenticate the user using token introspection.

        This first checks if the token is cached. If it's not cached, the token is looked
        up in Staff SSO. An adviser is then looked up using the retrieved token data.
        """
        try:
            authorization_header = request.headers['authorization']
        except KeyError as exc:
            raise AuthenticationFailed(NO_CREDENTIALS_MESSAGE) from exc

        scheme, _, token = authorization_header.partition(' ')

        if scheme.lower() != 'bearer':
            raise AuthenticationFailed(INCORRECT_SCHEME)

        if not token:
            raise AuthenticationFailed(NO_CREDENTIALS_MESSAGE)

        token_data, was_cached = _look_up_token(token, request)
        if not token_data:
            raise AuthenticationFailed(INVALID_CREDENTIALS_MESSAGE)

        user = _look_up_adviser(token_data)
        if not (user and user.is_active):
            raise AuthenticationFailed(INVALID_CREDENTIALS_MESSAGE)

        # Only record real (non-cached) introspections (otherwise we'd be recording every
        # request)
        if not was_cached:
            record_user_event(request, UserEventType.OAUTH_TOKEN_INTROSPECTION, adviser=user)

        return user, None


def _look_up_token(token, request) -> Tuple[Optional[dict], bool]:
    """Look up data about an access token.

    This first checks the cache, and falls back to querying Staff SSO if the token isn't cached.

    :returns: a 2-tuple of: (token data, was the token cached)
    """
    cached_token_data = get_token_data_from_cache(token)

    if cached_token_data:
        return cached_token_data, True

    try:
        introspection_data = introspect_token(token, request)
    except SSOInvalidTokenError:
        return None, False
    except SSORequestError:
        logger.exception('SSO introspection request failed')
        return None, False

    relative_expiry = _calculate_expiry(introspection_data['exp'])

    # This should not happen as expiry times should be in the future
    if relative_expiry <= 0:
        logger.warning('Introspected token has an expiry time in the past')
        return None, False

    cached_token_data = add_token_data_to_cache(
        token,
        introspection_data['username'],
        introspection_data['email_user_id'],
        relative_expiry,
    )
    return cached_token_data, False


def _look_up_adviser(cached_token_data):
    """Look up the adviser using data about an access token.

    The adviser is looked up using its SSO email user ID.
    """
    sso_email_user_id = cached_token_data['sso_email_user_id']

    try:
        return _get_adviser(sso_email_user_id=sso_email_user_id)
    except Advisor.DoesNotExist:
        return None


def _calculate_expiry(timestamp):
    expires_in = timestamp - time.time()
    return min(expires_in, settings.STAFF_SSO_USER_TOKEN_CACHING_PERIOD)


def _get_adviser(**kwargs):
    return Advisor.objects.select_related('dit_team').get(**kwargs)
