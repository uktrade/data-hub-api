from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from reversion.admin import VersionAdmin

from datahub.company.models import Advisor


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
