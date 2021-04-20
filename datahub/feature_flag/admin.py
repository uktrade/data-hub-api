from django.contrib import admin

from datahub.core.admin import BaseModelAdminMixin
from datahub.feature_flag.models import FeatureFlag, UserFeatureFlag


class BaseFeatureFlagAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """Base feature flag admin."""

    list_display = ('code', 'description', 'is_active', 'created_by', 'created_on')
    search_fields = ('code',)
    readonly_fields = (
        'id',
        'created',
        'modified',
    )
    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )


@admin.register(FeatureFlag)
class FeatureFlagAdmin(BaseFeatureFlagAdmin):
    """Feature flag admin."""


@admin.register(UserFeatureFlag)
class UserFeatureFlagAdmin(BaseFeatureFlagAdmin):
    """User feature flag admin."""
