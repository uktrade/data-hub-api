from django.contrib import admin

from datahub.core.admin import DisabledOnFilter
from . import models

MODELS_TO_REGISTER = (
    models.BusinessType,
    models.Sector,
    models.Country,
    models.Title,
    models.Role,
    models.InvestmentType,
    models.FDIType,
    models.NonFDIType,
    models.ReferralSourceActivity,
    models.ReferralSourceMarketing,
    models.ReferralSourceWebsite,
    models.InvestmentBusinessActivity,
    models.InvestmentStrategicDriver
)

MODELS_TO_REGISTER_DISABLEABLE = (
    models.Service,
    models.UKRegion,
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

    fields = ('name',)
    list_display = ('name',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')


@admin.register(*MODELS_TO_REGISTER_DISABLEABLE)
class DisableableMetadataAdmin(admin.ModelAdmin):
    """Custom Disableable Metadata Admin."""

    fields = ('name', 'disabled_on',)
    list_display = ('name', 'disabled_on',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(*MODELS_TO_REGISTER_WITH_ORDER)
class OrderedMetadataAdmin(admin.ModelAdmin):
    """Admin for ordered metadata models."""

    fields = ('name', 'order',)
    list_display = ('name', 'order',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')


@admin.register(models.Team)
class TeamAdmin(MetadataAdmin):
    """Team Admin."""

    fields = ('name', 'country', 'uk_region', 'role')
    list_display = ('name', 'role')
    list_select_related = ('role',)
    search_fields = ('name', 'pk')


@admin.register(models.TeamRole)
class TeamRoleAdmin(MetadataAdmin):
    """Team Admin."""

    fields = ('name', 'team_role_groups')
    list_display = ('name',)
    search_fields = ('name', 'pk')
    filter_horizontal = ('team_role_groups',)
