from django.contrib import admin

from datahub.core.admin import DisabledOnFilter
from . import models


MODELS_TO_REGISTER_DISABLEABLE = (
    models.BusinessType,
    models.CompanyClassification,
    models.Country,
    models.FDIType,
    models.FDIValue,
    models.HeadquarterType,
    models.InvestmentBusinessActivity,
    models.InvestmentStrategicDriver,
    models.InvestmentType,
    models.ReferralSourceActivity,
    models.ReferralSourceMarketing,
    models.ReferralSourceWebsite,
    models.Role,
    models.Sector,
    models.Service,
    models.Title,
    models.UKRegion,
)

MODELS_TO_REGISTER_WITH_ORDER = (
    models.EmployeeRange,
    models.TurnoverRange,
    models.SalaryRange,
    models.InvestmentProjectStage
)


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

    fields = ('name', 'order', 'disabled_on',)
    list_display = ('name', 'order', 'disabled_on',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    """Team Admin."""

    fields = ('name', 'country', 'uk_region', 'role', 'disabled_on',)
    list_display = ('name', 'role', 'disabled_on',)
    list_select_related = ('role',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(models.TeamRole)
class TeamRoleAdmin(admin.ModelAdmin):
    """Team Admin."""

    fields = ('name', 'groups', 'disabled_on',)
    list_display = ('name', 'disabled_on',)
    search_fields = ('name', 'pk')
    filter_horizontal = ('groups',)
    list_filter = (DisabledOnFilter,)
