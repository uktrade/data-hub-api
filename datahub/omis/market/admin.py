from django.contrib import admin

from datahub.omis.market.models import Market


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    """Market Admin."""

    fields = ('country', 'manager_email', 'disabled_on')
    list_display = ('country', 'manager_email', 'disabled_on')
    readonly_fields = ('country',)
    search_fields = ('country__name', )
