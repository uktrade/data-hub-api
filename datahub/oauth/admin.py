from django.contrib import admin

from datahub.oauth.models import OAuthApplicationScope


@admin.register(OAuthApplicationScope)
class OAuthApplicationScopeAdmin(admin.ModelAdmin):
    """OAuthApplicationScope Admin."""
