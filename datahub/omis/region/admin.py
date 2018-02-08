from django.contrib import admin

from .models import UKRegionalSettings


@admin.register(UKRegionalSettings)
class UKRegionalSettingsAdmin(admin.ModelAdmin):
    """UKRegionalSettings Admin."""

    fields = ('uk_region', 'manager_emails')
    list_display = ('uk_region', 'manager_emails')
    search_fields = ('uk_region__name', )
