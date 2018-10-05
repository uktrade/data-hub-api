from django.contrib import admin

from datahub.core.admin import BaseModelAdminMixin
from datahub.documents import models


@admin.register(models.Document)
class DocumentsAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """Documents admin."""

    list_display = (
        'id', 'name', 'uploaded_on', 'av_clean', 'scan_initiated_on', 'scanned_on',
    )
    raw_id_fields = (
        'archived_by',
    )
    list_filter = (
        'av_clean',
    )
    readonly_fields = (
        'created',
        'modified',
    )
    date_hierarchy = 'created_on'
    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )

    def get_actions(self, request):
        """Remove the delete selected action."""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        """Disable document deletion."""
        return False
