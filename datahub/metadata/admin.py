from django.contrib import admin

from . import models

MODELS_TO_REGISTER = (
    models.BusinessType,
    models.Sector,
    models.UKRegion,
    models.Country,
    models.Title,
    models.Role,
    models.TeamRole,
    models.Service,
    models.ServiceDeliveryStatus,
    models.Event,
    models.InvestmentType,
    models.FDIType,
    models.NonFDIType,
    models.ReferralSourceActivity,
    models.ReferralSourceMarketing,
    models.ReferralSourceWebsite,
    models.InvestmentBusinessActivity,
    models.InvestmentStrategicDriver
)

MODELS_TO_REGISTER_WITH_ORDER = (
    models.EmployeeRange,
    models.TurnoverRange,
    models.SalaryRange,
    models.InvestmentProjectStage
)


@admin.register(*MODELS_TO_REGISTER)
class MetadataAdmin(admin.ModelAdmin):
    """Custom Metadata Admin."""

    fields = ('name', )
    list_display = ('name', )
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')


@admin.register(*MODELS_TO_REGISTER_WITH_ORDER)
class OrderedMetadataAdmin(admin.ModelAdmin):
    """Admin for ordered metadata models."""

    fields = ('name', 'order', )
    list_display = ('name', 'order', )
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')


@admin.register(models.Team)
class TeamAdmin(MetadataAdmin):
    """Team Admin."""

    fields = ('name', 'country', 'uk_region', 'role')
    list_display = ('name', 'role')
    list_select_related = ('role', )
    search_fields = ('name', 'pk')
