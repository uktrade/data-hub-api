from oauth2_provider.scopes import BaseScopes


from datahub.core.utils import StrEnum
from datahub.oauth.models import OAuthApplicationScope


class Scope(StrEnum):
    """Defined OAuth scopes."""

    internal_front_end = 'data-hub:internal-front-end'
    public_omis_front_end = 'data-hub:public-omis-front-end'


SCOPES_DESCS = {
    Scope.internal_front_end.value: 'Endpoints used by the internal front end',
    Scope.public_omis_front_end.value: 'Endpoints used by the OMIS public front end',
}


class ApplicationScopesBackend(BaseScopes):
    """
    Custom django-oauth-toolkit scopes back end.

    This lets scopes be restricted by app. For background, see
    https://github.com/evonove/django-oauth-toolkit/pull/395.

    Similar functionality will probably eventually be included in django-oauth-toolkit,
    in which case this can be removed.

    See :class:`.BaseScopes` for further details on the methods.
    """

    def get_all_scopes(self) -> dict:
        """Gets a mapping of all scopes."""
        return SCOPES_DESCS

    def get_available_scopes(self, application=None, request=None, *args, **kwargs) -> set:
        """
        Gets all available scopes for an app during a request.

        Note: Returns a set as opposed to a frozenset, because oauthlib currently has explicit
        type checks.
        """
        try:
            app_scope = OAuthApplicationScope.objects.get(application=application)
            return set(app_scope.scopes) & self.get_all_scopes().keys()
        except OAuthApplicationScope.DoesNotExist:
            return set()

    def get_default_scopes(self, application=None, request=None, *args, **kwargs) -> set:
        """
        Gets the default scopes for an app.

        Currently returns all available scopes for the app.
        """
        return self.get_available_scopes(
            application=application, request=request, *args, **kwargs,
        )
