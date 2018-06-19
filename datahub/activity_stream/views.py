import logging

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.utils.crypto import constant_time_compare
from mohawk import Receiver
from mohawk.exc import HawkFail
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


logger = logging.getLogger(__name__)

NO_CREDENTIALS_MESSAGE = 'Authentication credentials were not provided.'
INCORRECT_CREDENTIALS_MESSAGE = 'Incorrect authentication credentials.'


def _lookup_credentials(access_key_id):
    if not constant_time_compare(access_key_id,
                                 settings.ACTIVITY_STREAM_ACCESS_KEY_ID):
        raise HawkFail(f'No Hawk ID of {access_key_id}')

    return {
        'id': settings.ACTIVITY_STREAM_ACCESS_KEY_ID,
        'key': settings.ACTIVITY_STREAM_SECRET_ACCESS_KEY,
        'algorithm': 'sha256',
    }


def _seen_nonce(access_key_id, nonce, _):
    cache_key = f'activity_stream:{access_key_id}:{nonce}'
    seen_cache_key = cache.get(cache_key, False)

    # cache.add only adds key if it isn't present
    cache.add(cache_key, True,
              timeout=settings.ACTIVITY_STREAM_NONCE_EXPIRY_SECONDS)

    if seen_cache_key:
        logger.warning(f'Already seen nonce {nonce}')

    return seen_cache_key


def _authorise(request):
    Receiver(
        _lookup_credentials,
        request.META['HTTP_AUTHORIZATION'],
        request.build_absolute_uri(),
        request.method,
        content=request.body,
        content_type=request.content_type,
        seen_nonce=_seen_nonce,
    )


class _ActivityStreamUser(AnonymousUser):
    username = 'activity_stream_user'

    @property
    def is_authenticated(self):
        return True


class _ActivityStreamAuthentication(BaseAuthentication):

    def authenticate_header(self, request):
        """This is returned as the WWW-Authenticate header when
        AuthenticationFailed is raised. DRF also requires this
        to send a 401 (as opposed to 403)
        """
        return 'Hawk'

    def authenticate(self, request):
        if 'HTTP_X_FORWARDED_FOR' not in request.META:
            logger.warning(
                'Failed authentication: no X-Forwarded-For header passed'
            )
            raise AuthenticationFailed(INCORRECT_CREDENTIALS_MESSAGE)

        x_forwarded_for = request.META['HTTP_X_FORWARDED_FOR']
        remote_address = x_forwarded_for.split(',', maxsplit=1)[0].strip()

        if remote_address not in settings.ACTIVITY_STREAM_IP_WHITELIST:
            logger.warning(
                'Failed authentication: the X-Forwarded-For header did not '
                'start with an IP in the whitelist'
            )
            raise AuthenticationFailed(INCORRECT_CREDENTIALS_MESSAGE)

        if 'HTTP_AUTHORIZATION' not in request.META:
            raise AuthenticationFailed(NO_CREDENTIALS_MESSAGE)

        try:
            _authorise(request)
        except HawkFail as e:
            logger.warning(f'Failed authentication {e}')
            raise AuthenticationFailed(INCORRECT_CREDENTIALS_MESSAGE)

        return (_ActivityStreamUser(), None)


class ActivityStreamViewSet(ViewSet):
    """List-only view set for the activity stream"""

    authentication_classes = (_ActivityStreamAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        """A single page of activities"""
        return Response({'secret': 'content-for-pen-test'})
