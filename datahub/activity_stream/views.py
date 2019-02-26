import logging

from django.conf import settings
from django.core.cache import cache
from django.utils.decorators import decorator_from_middleware
from mohawk import Receiver
from mohawk.exc import HawkFail
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from config.settings.types import HawkScope


logger = logging.getLogger(__name__)

NO_CREDENTIALS_MESSAGE = 'Authentication credentials were not provided.'
INCORRECT_CREDENTIALS_MESSAGE = 'Incorrect authentication credentials.'
PAAS_ADDED_X_FORWARDED_FOR_IPS = 2


def _lookup_credentials(access_key_id):
    """Raises HawkFail if the access key ID cannot be found."""
    try:
        credentials = settings.HAWK_RECEIVER_CREDENTIALS[access_key_id]
    except KeyError as exc:
        raise HawkFail(f'No Hawk ID of {access_key_id}') from exc

    return {
        'id': access_key_id,
        'algorithm': 'sha256',
        **credentials,
    }


def _seen_nonce(access_key_id, nonce, _):
    """Returns if the passed access_key_id/nonce combination has been
    used within settings.HAWK_RECEIVER_NONCE_EXPIRY_SECONDS
    """
    cache_key = f'hawk:{access_key_id}:{nonce}'

    # cache.add only adds key if it isn't present
    seen_cache_key = not cache.add(
        cache_key,
        True,
        timeout=settings.HAWK_RECEIVER_NONCE_EXPIRY_SECONDS,
    )

    if seen_cache_key:
        logger.warning(f'Already seen nonce {nonce}')

    return seen_cache_key


def _authorise(request):
    """Raises a HawkFail if the passed request cannot be authenticated"""
    return Receiver(
        _lookup_credentials,
        request.META['HTTP_AUTHORIZATION'],
        request.build_absolute_uri(),
        request.method,
        content=request.body,
        content_type=request.content_type,
        seen_nonce=_seen_nonce,
    )


class HawkAuthentication(BaseAuthentication):
    """DRF authentication class that uses Hawk authentication."""

    def authenticate_header(self, request):
        """This is returned as the WWW-Authenticate header when
        AuthenticationFailed is raised. DRF also requires this
        to send a 401 (as opposed to 403)
        """
        return 'Hawk'

    def authenticate(self, request):
        """Authenticates a request using two mechanisms:

        1. The X-Forwarded-For-Header, compared against a whitelist
        2. A Hawk signature in the Authorization header

        If either of these suggest we cannot authenticate, AuthenticationFailed
        is raised, as required in the DRF authentication flow
        """
        self._check_ip(request)
        return self._authenticate_by_hawk(request)

    def _check_ip(self, request):
        """Blocks incoming connections based on IP in X-Forwarded-For

        Ideally, this would be done at the network level. However, this is
        not possible in PaaS. However, they do always add two IPs, with
        the first one being the IP connection are made from, so we can
        check the second-from-the-end with some confidence it hasn't been
        spoofed.

        This wouldn't be able to be trusted in other environments, but we're
        not running in non-PaaS environments in production.
        """
        if 'HTTP_X_FORWARDED_FOR' not in request.META:
            logger.warning(
                'Failed authentication: no X-Forwarded-For header passed',
            )
            raise AuthenticationFailed(INCORRECT_CREDENTIALS_MESSAGE)

        x_forwarded_for = request.META['HTTP_X_FORWARDED_FOR']
        ip_addresses = x_forwarded_for.split(',')
        if len(ip_addresses) < PAAS_ADDED_X_FORWARDED_FOR_IPS:
            logger.warning(
                'Failed authentication: the X-Forwarded-For header does not '
                'contain enough IP addresses',
            )
            raise AuthenticationFailed(INCORRECT_CREDENTIALS_MESSAGE)

        # PaaS appends 2 IPs, where the IP connected from is the first
        remote_address = ip_addresses[-PAAS_ADDED_X_FORWARDED_FOR_IPS].strip()

        if remote_address not in settings.HAWK_RECEIVER_IP_WHITELIST:
            logger.warning(
                'Failed authentication: the X-Forwarded-For header was not '
                'produced by a whitelisted IP',
            )
            raise AuthenticationFailed(INCORRECT_CREDENTIALS_MESSAGE)

    def _authenticate_by_hawk(self, request):
        if 'HTTP_AUTHORIZATION' not in request.META:
            raise AuthenticationFailed(NO_CREDENTIALS_MESSAGE)

        try:
            hawk_receiver = _authorise(request)
        except HawkFail as e:
            logger.warning(f'Failed authentication {e}')
            raise AuthenticationFailed(INCORRECT_CREDENTIALS_MESSAGE)

        return None, hawk_receiver


class HawkResponseMiddleware:
    """Adds the Server-Authorization header to the response, so the originator
    of the request can authenticate the response
    """

    def process_response(self, view, response):
        """
        Sign Hawk responses.

        If the request was authenticated using Hawk, this adds the Server-Authorization header
        to the response, so the originator of the request can authenticate the response.
        """
        if isinstance(view.request.successful_authenticator, HawkAuthentication):
            response['Server-Authorization'] = view.request.auth.respond(
                content=response.content,
                content_type=response['Content-Type'],
            )
        return response


class HawkScopePermission(BasePermission):
    """
    Permission class to authorise Hawk requests using the allowed scope of the client.

    If the request was not authenticated using Hawk, access is denied.
    """

    def has_permission(self, request, view):
        """Checks if the client has the scope required by the view."""
        required_hawk_scope = getattr(view, 'required_hawk_scope', None)

        if required_hawk_scope is None:
            raise ValueError('required_hawk_scope was not set on the view')

        if not isinstance(request.successful_authenticator, HawkAuthentication):
            return False

        return required_hawk_scope == request.auth.resource.credentials['scope']


class ActivityStreamViewSet(ViewSet):
    """List-only view set for the activity stream."""

    authentication_classes = (HawkAuthentication,)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.activity_stream

    @decorator_from_middleware(HawkResponseMiddleware)
    def list(self, request):
        """A single page of activities"""
        return Response({'secret': 'content-for-pen-test'})
