import logging
from functools import partial

from django.conf import settings
from django.core.cache import cache
from mohawk import Receiver
from mohawk.exc import HawkFail
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


logger = logging.getLogger(__name__)

NO_CREDENTIALS_MESSAGE = 'Authentication credentials were not provided.'
INCORRECT_CREDENTIALS_MESSAGE = 'Incorrect authentication credentials.'


class HawkAuthentication(BaseAuthentication):
    """DRF authentication class that uses Hawk authentication."""

    def authenticate_header(self, request):
        """This is returned as the WWW-Authenticate header when
        AuthenticationFailed is raised. DRF also requires this
        to send a 401 (as opposed to 403)
        """
        return 'Hawk'

    def authenticate(self, request):
        """Authenticates a request using Hawk signature in the Authorization header

        If we cannot authenticate, AuthenticationFailed is raised, as required
        in the DRF authentication flow
        """
        if 'HTTP_AUTHORIZATION' not in request.META:
            raise AuthenticationFailed(NO_CREDENTIALS_MESSAGE)

        try:
            hawk_receiver = _authorise(request)
        except HawkFail as e:
            logger.warning(f'Failed authentication {e}')
            raise AuthenticationFailed(INCORRECT_CREDENTIALS_MESSAGE)

        return None, hawk_receiver


class HawkResponseSigningMixin:
    """
    DRF view mixin to add the Server-Authorization header to responses, so the originator
    of the request can authenticate the response.

    Must be first in the base class list so that the APIView method is overridden.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Add callback to sign Hawk responses.

        If the request was authenticated using Hawk, this adds a post-render callback to the
        response which sets the Server-Authorization header, so that the originator of the
        request can authenticate the response.
        """
        finalized_response = super().finalize_response(request, response, *args, **kwargs)
        callback = partial(_sign_rendered_response, request)
        finalized_response.add_post_render_callback(callback)
        return finalized_response


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

        return required_hawk_scope in request.auth.resource.credentials['scopes']


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


def _sign_rendered_response(request, response):
    if isinstance(request.successful_authenticator, HawkAuthentication):
        response['Server-Authorization'] = request.auth.respond(
            content=response.content,
            content_type=response['Content-Type'],
        )
    return response
