from django.contrib import admin

from reversion.admin import VersionAdmin

from .models import Interaction, ServiceDelivery


MODELS_TO_REGISTER = (Interaction, ServiceDelivery)

for model_cls in MODELS_TO_REGISTER:
    admin.site.register(model_cls, VersionAdmin)
