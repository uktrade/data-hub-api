from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django import forms


from reversion.admin import VersionAdmin

from . models import Advisor, Company, Contact, Interaction

MODELS_TO_REGISTER = (Advisor, Company, Contact, Interaction)

for model in MODELS_TO_REGISTER:
    admin.site.register(model, VersionAdmin)


class AdminLoginForm(AdminAuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autocomplete': 'off'}))


admin.site.login_form = AdminLoginForm
