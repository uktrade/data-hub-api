from time import time

from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect

from datahub.core.utils import reverse_with_query_string


class OAuthSessionMiddleware:
    """
    OAuthSessionMiddleware checks if user has been logged in via OAuth.
    """

    def __init__(self, get_response):
        """Get response."""
        self.get_response = get_response

    def __call__(self, request):
        """
        Check if OAuth2 expiration time is present in the session.

        If OAuth2 expires on has passed it means we have to logout the user.
        """
        if request.user.is_authenticated:
            oauth_expires_on = request.session.get('oauth.expires_on')
            if oauth_expires_on is not None and oauth_expires_on < time():
                django_logout(request)

                return redirect(reverse_with_query_string('admin:login', {'next': request.path}))

        return self.get_response(request)
