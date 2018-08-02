from django.contrib import admin

from datahub.core.admin import BaseModelAdminMixin
from datahub.feature_flag.models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """Feature flag admin."""

    list_display = ('code', 'description', 'is_active', 'created_by', 'created_on',)
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
