from django.contrib import admin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from datahub.oauth.admin_sso.views import login, logout


class OAuth2AdminSite(admin.AdminSite):
    """Replace login and logout views with corresponding OAuth2 views."""

    @method_decorator(never_cache)
    def login(self, request, extra_context=None):
        """Replace login view."""
        return login(request)

    @method_decorator(never_cache)
    def logout(self, request, extra_context=None):
        """Replace logout view."""
        return logout(request)
