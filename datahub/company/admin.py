from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin, ViewOnlyAdmin
from datahub.metadata.admin import DisableableMetadataAdmin
from .models import (
    Advisor,
    CompaniesHouseCompany,
    Company,
    CompanyCoreTeamMember,
    Contact,
    ExportExperienceCategory,
)


admin.site.register(ExportExperienceCategory, DisableableMetadataAdmin)


class CompanyCoreTeamMemberInline(admin.TabularInline):
    """Inline admin for CompanyCoreTeamMember"""

    model = CompanyCoreTeamMember
    fields = ('id', 'adviser', )
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
                )
            }
        ),
        (
            'HIERARCHY',
            {
                'fields': (
                    'headquarter_type',
                    'global_headquarters',
                )
            }
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
                )
            }
        ),
        (
            'EXPORT',
            {
                'fields': (
                    'export_experience_category',
                    'export_to_countries',
                    'future_interest_countries',
                )
            }
        ),
        (
            'LEGACY FIELDS',
            {
                'fields': (
                    'reference_code',
                    'account_manager',
                    'archived_documents_url_path',
                )
            }
        ),
        (
            'ARCHIVE',
            {
                'fields': (
                    'archived',
                    'archived_on',
                    'archived_by',
                    'archived_reason',
                )
            }
        )
    )
    search_fields = (
        'name',
        'id',
        'company_number',
    )
    raw_id_fields = (
        'global_headquarters',
        'one_list_account_owner',
        'account_manager',
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


@admin.register(CompaniesHouseCompany)
class CHCompany(ViewOnlyAdmin):
    """Companies House company admin."""

    search_fields = ['name', 'company_number']


@admin.register(Advisor)
class AdviserAdmin(VersionAdmin, UserAdmin):
    """Adviser admin."""

    fieldsets = (
        (None, {
            'fields': (
                'email',
                'password'
            )
        }),
        ('PERSONAL INFO', {
            'fields': (
                'first_name',
                'last_name',
                'contact_email',
                'telephone_number',
                'dit_team'
            )
        }),
        ('PERMISSIONS', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('IMPORTANT DATES', {
            'fields': (
                'last_login',
                'date_joined'
            )
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'dit_team', 'is_active', 'is_staff',)
    search_fields = (
        '=pk',
        'first_name',
        'last_name',
        'email',
        '=dit_team__pk',
        'dit_team__name',
    )
    ordering = ('email',)
