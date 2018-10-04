from django import forms
from django.contrib import admin
from django.db import models
from reversion.admin import VersionAdmin

from datahub.company.models import Company, CompanyCoreTeamMember
from datahub.core.admin import BaseModelAdminMixin


class CompanyCoreTeamMemberInline(admin.TabularInline):
    """Inline admin for CompanyCoreTeamMember"""

    model = CompanyCoreTeamMember
    fields = ('id', 'adviser')
    extra = 1
    formfield_overrides = {
        models.UUIDField: {'widget': forms.HiddenInput},
    }
    raw_id_fields = (
        'adviser',
    )


@admin.register(Company)
class CompanyAdmin(BaseModelAdminMixin, VersionAdmin):
    """Company admin."""

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'created',
                    'modified',
                    'name',
                    'alias',
                    'company_number',
                    'vat_number',
                    'description',
                    'website',
                    'business_type',
                    'sector',
                    'uk_region',
                    'employee_range',
                    'turnover_range',
                    'classification',
                    'one_list_account_owner',
                ),
            },
        ),
        (
            'HIERARCHY',
            {
                'fields': (
                    'headquarter_type',
                    'global_headquarters',
                ),
            },
        ),
        (
            'ADDRESS',
            {
                'fields': (
                    'registered_address_1',
                    'registered_address_2',
                    'registered_address_town',
                    'registered_address_county',
                    'registered_address_postcode',
                    'registered_address_country',

                    'trading_address_1',
                    'trading_address_2',
                    'trading_address_town',
                    'trading_address_county',
                    'trading_address_postcode',
                    'trading_address_country',
                ),
            },
        ),
        (
            'EXPORT',
            {
                'fields': (
                    'export_experience_category',
                    'export_to_countries',
                    'future_interest_countries',
                ),
            },
        ),
        (
            'LEGACY FIELDS',
            {
                'fields': (
                    'reference_code',
                    'archived_documents_url_path',
                ),
            },
        ),
        (
            'ARCHIVE',
            {
                'fields': (
                    'archived',
                    'archived_on',
                    'archived_by',
                    'archived_reason',
                ),
            },
        ),
    )
    search_fields = (
        'name',
        'id',
        'company_number',
    )
    raw_id_fields = (
        'global_headquarters',
        'one_list_account_owner',
        'archived_by',
    )
    readonly_fields = (
        'id',
        'created',
        'modified',
        'archived_documents_url_path',
        'reference_code',
    )
    list_display = (
        'name',
        'registered_address_country',
    )
    inlines = (
        CompanyCoreTeamMemberInline,
    )
