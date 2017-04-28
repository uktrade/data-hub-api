from django.contrib import admin

from reversion.admin import VersionAdmin

from datahub.investment.models import (InvestmentProject)


@admin.register(InvestmentProject)
class InvestmentProjectAdmin(VersionAdmin):
    """Investment project admin."""

    search_fields = ['name']
