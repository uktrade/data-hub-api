from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin
from datahub.export_win.models import Win


@admin.register(Win)
class WinAdmin(BaseModelAdminMixin, VersionAdmin):
    """Admin for Wins."""

    list_display = (
        'id',
        'get_adviser',
        'get_company',
        'get_contact_names',
        'lead_officer',
        'country',
        'sector',
        'get_date_confirmed',
        'created_on',
    )
    list_filter = (
        ('created_on', DateFieldListFilter),
    )
    readonly_fields = (
        'id',
        'created_on',
        'modified_on',
    )
    search_fields = (
        'adviser__name',
        'company__name',
        'pk',
    )
    list_select_related = (
        'adviser',
        'company',
    )
    raw_id_fields = (
        'adviser',
        'company',
    )

    def get_adviser(self, obj):
        """Return adviser as user with email."""
        return f'{obj.adviser} <{obj.adviser.email}>'
    get_adviser.short_description = 'User'

    def get_company(self, obj):
        """Return company name."""
        return obj.company
    get_company.short_description = 'Organisation or Company name'

    def get_date_confirmed(self, obj):
        """Return wins being confirmed."""
        return obj.customer_response.responded_on
    get_date_confirmed.short_description = 'Date win confirmed'

    def get_contact_names(self, obj):
        """Return a comma separated list of company contact names."""
        return ', '.join(contact.name for contact in obj.company_contacts.all())
    get_contact_names.short_description = 'Contact name'
