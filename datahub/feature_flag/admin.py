from django.contrib import admin

from datahub.feature_flag.models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    """Feature flag admin."""

    list_display = ('code', 'description', 'is_active', 'created_by', 'created_on',)
    search_fields = ('code',)
    readonly_fields = (
        'id',
        'created_by',
        'created_on',
        'modified_by',
        'modified_on',
    )
    raw_id_fields = (
        'created_by',
        'modified_by',
    )

    def save_model(self, request, obj, form, change):
        """
        Populate created_by/modified_by from the logged in user.
        """
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user

        super().save_model(request, obj, form, change)
