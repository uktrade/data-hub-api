from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from reversion.admin import VersionAdmin

from datahub.company.models import CompanyExport

from datahub.core.admin import BaseModelAdminMixin


@admin.register(CompanyExport)
class CompanyExportAdmin(BaseModelAdminMixin, VersionAdmin):
    """Company export admin."""

    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )
