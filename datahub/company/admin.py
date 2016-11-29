from django import forms
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.admin import UserAdmin

from reversion.admin import VersionAdmin

from . models import Advisor, Company, Contact, Interaction

MODELS_TO_REGISTER = (Company, Contact, Interaction)

for model_cls in MODELS_TO_REGISTER:
    admin.site.register(model_cls, VersionAdmin)


@admin.register(Advisor)
class AdvisorAdmin(VersionAdmin, UserAdmin):
    """Advisor admin."""

    def reversion_register(self, model, **kwargs):
        """Exclude last login from reversion changesets."""
        kwargs['exclude'] = ('last_login', )

        super().reversion_register(model, **kwargs)


class AdminLoginForm(AdminAuthenticationForm):
    """Admin login form override class."""

    username = forms.CharField(widget=forms.TextInput(attrs={'autocomplete': 'off'}))


admin.site.login_form = AdminLoginForm
