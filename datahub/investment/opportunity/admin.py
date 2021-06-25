from django.contrib import admin

from datahub.investment.opportunity import models


@admin.register(models.LargeCapitalOpportunity)
class LargeCapitalOpportunityAdmin(admin.ModelAdmin):
    """Large capital opportunity admin."""

    autocomplete_fields = (
        'uk_region_locations',
        'promoters',
        'other_dit_contacts',
        'investment_projects',
    )
    list_display = ('name',)
    search_fields = ('name', 'id')
    readonly_fields = ('id', 'created_by', 'modified_by')
