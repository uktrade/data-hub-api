from django.contrib import admin

from . import models

MODELS_TO_REGISTER = (
    models.BusinessType,
    models.InteractionType,
    models.Sector,
    models.EmployeeRange,
    models.TurnoverRange,
    models.UKRegion,
    models.Country,
    models.Title,
    models.Role,
    models.Team,
    models.Service
)

for model in MODELS_TO_REGISTER:
    admin.site.register(model)
