from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from reversion.admin import VersionAdmin

from datahub.core.admin import DisabledOnFilter, ReadOnlyAdmin
from .models import Advisor, CompaniesHouseCompany, Company, Contact, ExportExperienceCategory


@admin.register(ExportExperienceCategory)
class MetadataAdmin(admin.ModelAdmin):
    """Export experience category admin."""

    fields = ('id', 'name', 'disabled_on', )
    list_display = ('name', 'disabled_on', )
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(Company)
class CompanyAdmin(VersionAdmin):
    """Company admin."""

    search_fields = (
        'name',
        'id',
        'company_number',
    )
    raw_id_fields = (
        'parent',
        'global_headquarters',
        'one_list_account_owner',
        'account_manager',
        'archived_by',
        'created_by',
        'modified_by',
    )
    readonly_fields = (
        'archived_documents_url_path',
        'reference_code',
    )
    list_display = (
        'name',
        'registered_address_country',
    )


@admin.register(Contact)
class ContactAdmin(VersionAdmin):
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
        'created_by',
        'modified_by',
    )
    readonly_fields = (
        'archived_documents_url_path',
    )
    list_display = (
        '__str__',
        'company',
    )


@admin.register(CompaniesHouseCompany)
class CHCompany(ReadOnlyAdmin):
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
        ('Personal info', {
            'fields': (
                'first_name',
                'last_name',
                'contact_email',
                'telephone_number',
                'dit_team'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Important dates', {
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
