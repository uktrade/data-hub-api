from django.contrib import admin
from reversion.admin import VersionAdmin

from datahub.company.models import CompanyExport
from datahub.core.admin import BaseModelAdminMixin


@admin.register(CompanyExport)
class CompanyExportAdmin(BaseModelAdminMixin, VersionAdmin):
    """Company export admin."""
