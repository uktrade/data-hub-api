from django.contrib import admin

from datahub.company.models import CompanyExportCountry
from datahub.core.admin import BaseModelAdminMixin


class CompanyExportCountryAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """CompanyExportCountry Admin"""

    raw_id_fields = (
        'company',
    )
    list_select_related = (
        'company',
        'country',
    )


admin.site.register(CompanyExportCountry, CompanyExportCountryAdmin)
