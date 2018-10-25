from functools import partial

from django import forms
from django.contrib import admin
from django.db import models
from django.urls import path
from reversion.admin import VersionAdmin

from datahub.company.admin.merge.constants import MERGE_COMPANY_TOOL_FEATURE_FLAG
from datahub.company.admin.merge.step_1 import merge_select_other_company
from datahub.company.admin.merge.step_2 import select_primary_company
from datahub.company.admin.merge.step_3 import confirm_merge
from datahub.company.models import Company, CompanyCoreTeamMember
from datahub.core.admin import BaseModelAdminMixin
from datahub.feature_flag.utils import is_feature_flag_active


class CompanyCoreTeamMemberInline(admin.TabularInline):
    """Inline admin for CompanyCoreTeamMember"""

    model = CompanyCoreTeamMember
    fields = ('id', 'adviser')
    extra = 1
    formfield_overrides = {
        models.UUIDField: {'widget': forms.HiddenInput},
    }
    raw_id_fields = (
        'adviser',
    )


@admin.register(Company)
class CompanyAdmin(BaseModelAdminMixin, VersionAdmin):
    """Company admin."""

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'created',
                    'modified',
                    'name',
                    'alias',
                    'company_number',
                    'vat_number',
                    'description',
                    'website',
                    'business_type',
                    'sector',
                    'uk_region',
                    'employee_range',
                    'turnover_range',
                    'classification',
                    'one_list_account_owner',
                ),
            },
        ),
        (
            'HIERARCHY',
            {
                'fields': (
                    'headquarter_type',
                    'global_headquarters',
                ),
            },
        ),
        (
            'ADDRESS',
            {
                'fields': (
                    'registered_address_1',
                    'registered_address_2',
                    'registered_address_town',
                    'registered_address_county',
                    'registered_address_postcode',
                    'registered_address_country',

                    'trading_address_1',
                    'trading_address_2',
                    'trading_address_town',
                    'trading_address_county',
                    'trading_address_postcode',
                    'trading_address_country',
                ),
            },
        ),
        (
            'EXPORT',
            {
                'fields': (
                    'export_experience_category',
                    'export_to_countries',
                    'future_interest_countries',
                ),
            },
        ),
        (
            'LEGACY FIELDS',
            {
                'fields': (
                    'reference_code',
                    'archived_documents_url_path',
                ),
            },
        ),
        (
            'ARCHIVE',
            {
                'fields': (
                    'archived',
                    'archived_on',
                    'archived_by',
                    'archived_reason',
                ),
            },
        ),
    )
    search_fields = (
        'name',
        'id',
        'company_number',
    )
    raw_id_fields = (
        'global_headquarters',
        'one_list_account_owner',
        'archived_by',
    )
    readonly_fields = (
        'id',
        'created',
        'modified',
        'archived_documents_url_path',
        'reference_code',
    )
    list_display = (
        'name',
        'registered_address_country',
    )
    inlines = (
        CompanyCoreTeamMemberInline,
    )

    def get_urls(self):
        """Gets the URLs for this model."""
        model_meta = self.model._meta

        return [
            path(
                'merge-select-other-company/',
                self.admin_site.admin_view(partial(merge_select_other_company, self)),
                name=f'{model_meta.app_label}_'
                     f'{model_meta.model_name}_merge-select-other-company',
            ),
            path(
                'merge-select-primary-company/',
                self.admin_site.admin_view(partial(select_primary_company, self)),
                name=f'{model_meta.app_label}_'
                     f'{model_meta.model_name}_merge-select-primary-company',
            ),
            path(
                'merge-confirm/',
                self.admin_site.admin_view(partial(confirm_merge, self)),
                name=f'{model_meta.app_label}_'
                     f'{model_meta.model_name}_merge-confirm',
            ),
            *super().get_urls(),
        ]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Change view with additional data added to the context.

        Based on this example in the Django docs:
        https://docs.djangoproject.com/en/2.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.changelist_view
        """
        merge_company_tool_feature_flag = is_feature_flag_active(MERGE_COMPANY_TOOL_FEATURE_FLAG)
        extra_context = {
            **({} if extra_context is None else extra_context),
            'merge_company_tool_feature_flag': merge_company_tool_feature_flag,
        }

        return super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=extra_context,
        )
