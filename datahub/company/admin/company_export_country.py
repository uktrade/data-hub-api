
from django.contrib import admin
from datahub.core.admin import BaseModelAdminMixin
from reversion.admin import VersionAdmin
from datahub.company.models import CompanyExportCountry


class CompanyExportCountryAdmin(BaseModelAdminMixin, VersionAdmin):

    raw_id_fields = (
        'company',
    )
    list_select_related = (
        'company',
        'country',
    )


admin.site.register(CompanyExportCountry, CompanyExportCountryAdmin)
