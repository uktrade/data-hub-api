from django.contrib import admin
from reversion.admin import VersionAdmin

from datahub.company.models import Contact
from datahub.core.admin import BaseModelAdminMixin


@admin.register(Contact)
class ContactAdmin(BaseModelAdminMixin, VersionAdmin):
    """Contact admin."""

    search_fields = (
        'pk',
        'first_name',
        'last_name',
        'company__pk',
        'company__name',
    )
    raw_id_fields = (
        'company',
        'adviser',
        'archived_by',
    )
    readonly_fields = (
        'created',
        'modified',
        'archived_documents_url_path',
    )
    list_display = (
        '__str__',
        'company',
    )
    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )
