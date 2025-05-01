from django.contrib import admin
from reversion.admin import VersionAdmin

from datahub.company_activity.models import IngestedFile, KingsAwardRecipient
from datahub.core.admin import BaseModelAdminMixin


class IngestedFileAdmin(admin.ModelAdmin):
    search_fields = [
        'id',
        'created_on',
        'filepath',
        'file_created',
    ]
    list_display = [
        'id',
        'created_on',
        'filepath',
        'file_created',
    ]
    readonly_fields = [
        'id',
        'created_on',
    ]
    fieldsets = [
        (
            None,
            {
                'fields': [
                    'id',
                    'created_on',
                    'filepath',
                    'file_created',
                ],
            },
        ),
    ]


admin.site.register(IngestedFile, IngestedFileAdmin)


@admin.register(KingsAwardRecipient)
class KingsAwardRecipientAdmin(BaseModelAdminMixin, VersionAdmin):
    """Admin interface for managing King's Award Recipients."""

    list_display = ('company', 'year_awarded', 'category', 'year_expired', 'modified_on')
    list_filter = ('year_awarded', 'category', 'archived')
    search_fields = ('id', 'company__id', 'company__name', 'year_awarded')
    raw_id_fields = ('company', 'archived_by')

    ordering = ('-year_awarded', 'company__name')

    readonly_fields = ('id', 'created', 'modified', 'archived_on', 'archived_by')
    exclude = ('created_on', 'created_by', 'modified_on', 'modified_by')

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'company',
                    'year_awarded',
                    'category',
                    'citation',
                    'year_expired',
                ),
            },
        ),
        (
            'Audit',
            {
                'fields': ('created', 'modified'),
            },
        ),
        (
            'Archiving',
            {
                'fields': ('archived', 'archived_on', 'archived_by', 'archived_reason'),
                'classes': ('collapse',),
            },
        ),
    )
