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


@admin.register(*MODELS_TO_REGISTER)
class MetadataAdmin(admin.ModelAdmin):
    """Custom Metadata Admin."""

    fields = ('name', 'selectable')
    list_display = ('name', 'selectable')
    readonly_fields = ('id', )
