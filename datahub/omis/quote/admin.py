from django.contrib import admin

from datahub.omis.quote.models import TermsAndConditions


@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(admin.ModelAdmin):
    """Admin for TermsAndConditions."""

    fields = (
        'id',
        'name',
        'created_on',
        'content',
    )
    list_display = (
        'name',
        'created_on',
    )
    readonly_fields = (
        'id',
        'created_on',
    )
    actions = None

    def has_delete_permission(self, request, obj=None):
        """Records cannot be deleted."""
        return False

    def get_readonly_fields(self, request, obj=None):
        """Records cannot be changed after creation."""
        if obj and obj.pk:
            return self.fields
        return self.readonly_fields
