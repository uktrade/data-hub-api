from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from datahub.core.admin import DisabledOnFilter, ViewAndChangeOnlyAdmin, ViewOnlyAdmin
from datahub.metadata import models


MODELS_TO_REGISTER_DISABLEABLE = (
    models.FDIType,
    models.InvestmentBusinessActivity,
    models.InvestmentStrategicDriver,
    models.ReferralSourceActivity,
    models.ReferralSourceMarketing,
    models.ReferralSourceWebsite,
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
    models.InvestmentType,
    models.OverseasRegion,
    models.SectorCluster,
)

MODELS_TO_REGISTER_EDITABLE_ORDER_ONLY = (
    models.HeadquarterType,
)


class DisableableMetadataAdmin(admin.ModelAdmin):
    """
    Generic admin for disableable metadata models.

    Intended to be used across apps.
    """

    fields = ('id', 'name', 'disabled_on')
    list_display = ('name', 'disabled_on')
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


class ReadOnlyMetadataAdmin(ViewOnlyAdmin):
    """
    Generic admin for metadata models that shouldn't be edited.

    Intended to be used across apps.
    """

    list_display = ('name', 'disabled_on')
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


class OrderedMetadataAdmin(admin.ModelAdmin):
    """
    Generic admin for ordered metadata models.

    Intended to be used across apps.
    """

    fields = ('id', 'name', 'order', 'disabled_on')
    list_display = ('name', 'order', 'disabled_on')
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


class EditableOrderOnlyOrderedMetadataAdmin(OrderedMetadataAdmin, ViewAndChangeOnlyAdmin):
    """
    Generic admin for ordered metadata models with editable order.

    Intended to be used across apps.
    """

    readonly_fields = ('id', 'name', 'disabled_on')


admin.site.register(MODELS_TO_REGISTER_DISABLEABLE, DisableableMetadataAdmin)
admin.site.register(MODELS_TO_REGISTER_READ_ONLY, ReadOnlyMetadataAdmin)
admin.site.register(MODELS_TO_REGISTER_WITH_ORDER, OrderedMetadataAdmin)
admin.site.register(
    MODELS_TO_REGISTER_EDITABLE_ORDER_ONLY,
    EditableOrderOnlyOrderedMetadataAdmin,
)


@admin.register(models.Country)
class CountryAdmin(ViewOnlyAdmin):
    """Admin for countries."""

    fields = ('pk', 'name', 'overseas_region', 'disabled_on', 'iso_alpha2_code')
    list_display = ('name', 'overseas_region', 'disabled_on', 'iso_alpha2_code')
    search_fields = ('name', 'pk', 'iso_alpha2_code')
    list_filter = (DisabledOnFilter, 'overseas_region')


@admin.register(models.Service)
class ServiceAdmin(DisableableMetadataAdmin):
    """Admin for services."""

    fields = ('id', 'name', 'contexts', 'disabled_on')
    list_display = ('name', 'get_contexts_display', 'disabled_on')


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    """Team Admin."""

    fields = ('id', 'name', 'country', 'uk_region', 'role', 'tags', 'disabled_on')
    list_display = ('name', 'role', 'get_tags_display', 'disabled_on')
    list_select_related = ('role',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(models.TeamRole)
class TeamRoleAdmin(admin.ModelAdmin):
    """Team Admin."""

    fields = ('id', 'name', 'groups', 'disabled_on')
    list_display = ('name', 'disabled_on')
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    filter_horizontal = ('groups',)
    list_filter = (DisabledOnFilter,)


@admin.register(models.Sector)
class SectorAdmin(MPTTModelAdmin):
    """Sector admin."""

    fields = ('id', 'segment', 'parent', 'disabled_on')
    list_display = ('segment', 'disabled_on')
    readonly_fields = ('id',)
    search_fields = ('segment', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(models.InvestmentProjectStage)
class InvestmentProjectStageAdmin(ViewOnlyAdmin):
    """Investment project stage admin."""

    list_display = ('name', 'disabled_on', 'exclude_from_investment_flow')
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)
