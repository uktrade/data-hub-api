from django.contrib import admin

from datahub.core.admin import DisabledOnFilter
from datahub.featureflag.models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    """Feature flag admin."""

    fields = ('id', 'name', 'description', 'disabled_on',)
    list_display = ('name', 'description', 'created_by', 'created_on', 'disabled_on',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk',)
    list_filter = (DisabledOnFilter,)
