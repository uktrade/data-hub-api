from django.contrib import admin

from datahub.core.admin import ExportWinsAdminMixin

from datahub.investment.investor_profile import models


@admin.register(models.LargeCapitalInvestorProfile)
class LargeCapitalInvestorProfileAdmin(ExportWinsAdminMixin, admin.ModelAdmin):
    """Large capital investor profile admin."""

    autocomplete_fields = (
        'uk_region_locations',
        'other_countries_being_considered',
    )
    raw_id_fields = ('investor_company',)
    list_display = ('investor_company',)
    search_fields = ('investor_company__name', 'id')
    readonly_fields = ('id', 'created_by', 'modified_by')
