from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from reversion.admin import VersionAdmin

from datahub.company.models import CompanyExport
from datahub.company.validators import (
    validate_team_member_max_count,
)
from datahub.core.admin import BaseModelAdminMixin


class CompanyExportAdminForm(forms.ModelForm):
    def clean(self):
        super().clean()

        validate_team_member_max_count(
            self.cleaned_data.get('team_members'),
            ValidationError,
            wrapper_obj_name='team_members',
        )

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
    search_fields = (
        'title',
        'id',
        'company__pk',
        'owner__pk',
    )
    autocomplete_fields = (
        'company',
        'contacts',
        'owner',
        'team_members',
    )
    read_only_fields = (
        'id',
    )
    list_display = (
        'title',
        'company',
        'owner',
    )
    form = CompanyExportAdminForm
