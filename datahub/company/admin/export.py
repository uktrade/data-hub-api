from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from reversion.admin import VersionAdmin

from datahub.company.models import CompanyExport
from datahub.company.validators import (
    EXCEEDED_MAX_TEAM_MEMBER_COUNT,
    has_team_member_count_exceeded_max_allowed,
)
from datahub.core.admin import BaseModelAdminMixin


class CompanyExportAdminForm(forms.ModelForm):
    def clean(self):
        super().clean()

        if has_team_member_count_exceeded_max_allowed(self.cleaned_data.get('team_members')):
            raise ValidationError({'team_members': EXCEEDED_MAX_TEAM_MEMBER_COUNT})

    class Meta:
        model = CompanyExport
        exclude = []  # fields are specified in CompanyExportAdmin


@admin.register(CompanyExport)
class CompanyExportAdmin(BaseModelAdminMixin, VersionAdmin):
    """Company export admin."""

    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )
    form = CompanyExportAdminForm
