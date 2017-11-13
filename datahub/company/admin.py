from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from datahub.core.admin import BaseModelVersionAdmin
from .models import Advisor, CompaniesHouseCompany, Company, Contact


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


@admin.register(CompaniesHouseCompany)
class CHCompany(admin.ModelAdmin):
    """Companies House company admin."""

    search_fields = ['name', 'company_number']

    def get_readonly_fields(self, request, obj=None):
        """All fields readonly."""
        readonly_fields = list(set(
            [field.name for field in self.opts.local_fields] +
            [field.name for field in self.opts.local_many_to_many]
        ))
        if 'is_submitted' in readonly_fields:
            readonly_fields.remove('is_submitted')
        return readonly_fields


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
