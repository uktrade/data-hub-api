from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from datahub.core.admin import DisabledOnFilter, ReadOnlyAdmin
from . import models


MODELS_TO_REGISTER_DISABLEABLE = (
    models.CompanyClassification,
    models.Country,
    models.FDIType,
    models.InvestmentBusinessActivity,
    models.InvestmentStrategicDriver,
    models.ReferralSourceActivity,
    models.ReferralSourceMarketing,
    models.ReferralSourceWebsite,
    models.Role,
    models.Service,
    models.Title,
    models.UKRegion,
)

MODELS_TO_REGISTER_WITH_ORDER = (
    models.EmployeeRange,
    models.FDIValue,
    models.TurnoverRange,
    models.SalaryRange,
)

MODELS_TO_REGISTER_READ_ONLY = (
    models.BusinessType,
    models.HeadquarterType,
    models.InvestmentType,
    models.InvestmentProjectStage,
)


@admin.register(*MODELS_TO_REGISTER_DISABLEABLE)
class DisableableMetadataAdmin(admin.ModelAdmin):
    """Custom Disableable Metadata Admin."""

    fields = ('id', 'name', 'disabled_on',)
    list_display = ('name', 'disabled_on',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(*MODELS_TO_REGISTER_READ_ONLY)
class ReadOnlyMetadataAdmin(ReadOnlyAdmin):
    """Admin for metadata models that shouldn't be edited."""

    list_display = ('name', 'disabled_on',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(*MODELS_TO_REGISTER_WITH_ORDER)
class OrderedMetadataAdmin(admin.ModelAdmin):
    """Admin for ordered metadata models."""

    fields = ('id', 'name', 'order', 'disabled_on',)
    list_display = ('name', 'order', 'disabled_on',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    """Team Admin."""

    fields = ('id', 'name', 'country', 'uk_region', 'role', 'disabled_on',)
    list_display = ('name', 'role', 'disabled_on',)
    list_select_related = ('role',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(models.TeamRole)
class TeamRoleAdmin(admin.ModelAdmin):
    """Team Admin."""

    fields = ('id', 'name', 'groups', 'disabled_on',)
    list_display = ('name', 'disabled_on',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    filter_horizontal = ('groups',)
    list_filter = (DisabledOnFilter,)


@admin.register(models.Sector)
class SectorAdmin(MPTTModelAdmin):
    """Sector admin."""

    fields = ('id', 'segment', 'parent', 'disabled_on',)
    list_display = ('segment', 'disabled_on',)
    readonly_fields = ('id',)
    search_fields = ('segment', 'pk')
    list_filter = (DisabledOnFilter,)
