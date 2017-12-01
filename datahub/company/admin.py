from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from datahub.core.admin import BaseModelVersionAdmin, DisabledOnFilter, ReadOnlyAdmin
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
class CompanyAdmin(BaseModelVersionAdmin):
    """Company admin."""

    search_fields = (
        'name',
        'id',
        'company_number',
    )
    raw_id_fields = (
        'parent',
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


@admin.register(Contact)
class ContactAdmin(BaseModelVersionAdmin):
    """Contact admin."""

    search_fields = (
        'first_name',
        'last_name',
        'company__name'
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


@admin.register(CompaniesHouseCompany)
class CHCompany(ReadOnlyAdmin):
    """Companies House company admin."""

    search_fields = ['name', 'company_number']


@admin.register(Advisor)
class AdviserAdmin(BaseModelVersionAdmin, UserAdmin):
    """Adviser admin."""

    reversion_excluded_fields = BaseModelVersionAdmin.reversion_excluded_fields + ('last_login',)
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
    list_display = ('email', 'first_name', 'last_name', 'is_staff',)
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)
    actions = ['enable_users', 'disable_users']
