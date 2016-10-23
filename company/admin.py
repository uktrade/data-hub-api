from django.contrib import admin

from reversion.admin import VersionAdmin

from . models import Advisor, Company, Contact, Interaction


MODELS_TO_REGISTER = (Advisor, Company, Contact, Interaction)

for model in MODELS_TO_REGISTER:
    admin.site.register(model, VersionAdmin)
