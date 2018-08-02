from django.contrib import admin

from datahub.core.admin import BaseModelAdminMixin
from datahub.documents import models


@admin.register(models.Document)
class DocumentsAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """Documents admin."""

    list_display = (
        'id', 'path', 'uploaded_on', 'av_clean', 'scan_initiated_on', 'scanned_on',
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
