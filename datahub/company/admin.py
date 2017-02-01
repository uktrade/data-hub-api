from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from reversion.admin import VersionAdmin

from .models import Advisor, Company, Contact, Interaction

MODELS_TO_REGISTER = (Company, Contact, Interaction)

for model_cls in MODELS_TO_REGISTER:
    admin.site.register(model_cls, VersionAdmin)


@admin.register(Advisor)
class AdvisorAdmin(VersionAdmin, UserAdmin):
    """Advisor admin."""

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                       'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }), )
    add_fieldsets = ((None, {
        'classes': ('wide', ),
        'fields': ('email', 'password1', 'password2'),
    }), )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email', )

    def reversion_register(self, model, **kwargs):
        """Exclude last login from reversion changesets."""
        kwargs['exclude'] = ('last_login', )

        super().reversion_register(model, **kwargs)
