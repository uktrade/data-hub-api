from django.contrib.admin.apps import AdminConfig


class OAuthAdminConfig(AdminConfig):
    """Required to override stock Django admin app with OAuth2 admin app."""

    default_site = 'datahub.oauth.admin_sso.admin.OAuth2AdminSite'
