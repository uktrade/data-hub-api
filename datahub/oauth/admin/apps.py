from django.apps import AppConfig


class OAuthAdminConfig(AppConfig):
    """Required to register the OAuth admin access as Django app"""

    name = 'datahub.oauth.admin'

    label = 'oauth_admin'
