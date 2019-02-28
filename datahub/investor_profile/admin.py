from django.contrib import admin

from datahub.investor_profile import models


@admin.register(models.InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    """Investor profile admin."""

    list_display = ('investor_company', 'profile_type')
    search_fields = ('investor_company', 'pk')
