from django.contrib import admin

from reversion.admin import VersionAdmin

from . models import Company, Contact, Interaction

MODELS_TO_REGISTER = (Company, Contact, Interaction)

for model in MODELS_TO_REGISTER:
    admin.site.register(model, VersionAdmin)
