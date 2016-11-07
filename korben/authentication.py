from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .utils import generate_signature, get_korben_user


class KorbenSharedSecretAuthentication(BaseAuthentication):

    def authenticate(self, request):
        """Use a shared secret to perform authentication.

        - If authentication is not attempted, return None.
        - If authentication is attempted but fails, raise a AuthenticationFailed exception.
        """

        expected_signature = generate_signature(request.path, request.body, settings.DATAHUB_SECRET)
        offered_signature = request.META.get('X-Signature', '')
        if not offered_signature:
            return None
        if constant_time_compare(expected_signature, offered_signature):
            return get_korben_user(), None
        raise AuthenticationFailed('Shared secret authentication failed')
