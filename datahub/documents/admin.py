from django.contrib import admin

from datahub.documents import models


@admin.register(models.Document)
class DocumentsAdmin(admin.ModelAdmin):
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
    date_hierarchy = 'created_on'
