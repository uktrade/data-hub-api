from django.contrib import admin

from datahub.company.models import CompaniesHouseCompany
from datahub.core.admin import ViewOnlyAdmin


@admin.register(CompaniesHouseCompany)
class CHCompany(ViewOnlyAdmin):
    """Companies House company admin."""

    search_fields = ['name', 'company_number']
