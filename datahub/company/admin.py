from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from reversion.admin import VersionAdmin

from . models import Advisor, CompaniesHouseCompany, Company, Contact


@admin.register(Company)
class CompanyAdmin(VersionAdmin):
    """Company admin."""

    search_fields = ['name', 'id', 'company_number']


@admin.register(Contact)
class ContactAdmin(VersionAdmin):
    """Contact admin."""

    search_fields = ['first_name', 'last_name', 'company__name']


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
class AdvisorAdmin(VersionAdmin, UserAdmin):
    """Advisor admin."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'enabled')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email', )
    actions = ['enable_users', 'disable_users']

    def reversion_register(self, model, **kwargs):
        """Exclude last login from reversion changesets."""
        kwargs['exclude'] = ('last_login', )

        super().reversion_register(model, **kwargs)

    def enable_users(self, request, queryset):
        """Enable users for login."""
        queryset.update(enabled=True)
    enable_users.short_description = 'Enable users'

    def disable_users(self, request, queryset):
        """Disable users for login."""
        queryset.update(enabled=False)
    disable_users.short_description = 'Disable users.'