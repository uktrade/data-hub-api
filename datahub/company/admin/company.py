from django import forms
from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import gettext_lazy
from reversion.admin import VersionAdmin

from datahub.company.models import Company, CompanyCoreTeamMember
from datahub.core.admin import BaseModelAdminMixin, RawIdWidget
from datahub.feature_flag.utils import feature_flagged_view, is_feature_flag_active

MERGE_COMPANY_TOOL_FEATURE_FLAG = 'admin-merge-company-tool'


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


class SelectOtherCompanyForm(forms.Form):
    """Form used for selecting a second company when merging duplicate companies."""

    BOTH_COMPANIES_ARE_THE_SAME_MSG = gettext_lazy(
        'The two companies to merge cannot be the same. Please select a different company.',
    )

    other_company = forms.ModelChoiceField(
        Company.objects.all(),
        widget=RawIdWidget(Company),
    )

    def __init__(self, first_company_id, *args, **kwargs):
        """Initialises the form, saving the ID of the company already selected."""
        super().__init__(*args, **kwargs)
        self._first_company_id = first_company_id

    def clean_other_company(self):
        """Checks that a different company than the one navigated from has been selected."""
        other_company = self.cleaned_data['other_company']
        if str(other_company.pk) == str(self._first_company_id):
            raise ValidationError(self.BOTH_COMPANIES_ARE_THE_SAME_MSG)
        return other_company


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
                '<path:object_id>/merge-select-other-company/',
                self.admin_site.admin_view(self.merge_select_other_company),
                name=f'{model_meta.app_label}_'
                     f'{model_meta.model_name}_merge-select-other-company',
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

    @feature_flagged_view(MERGE_COMPANY_TOOL_FEATURE_FLAG)
    def merge_select_other_company(self, request, object_id):
        """
        First view as part of the merge duplicate companies process.

        Used to select the second company of the two to merge.

        As this does not modify state, the form is submitted using GET rather than POST.
        """
        if not self.has_change_permission(request):
            raise PermissionDenied

        template_name = 'admin/company/company/merge_select_other_company.html'
        title = gettext_lazy('Merge with another company')

        obj = self.get_object(request, unquote(object_id))
        form = SelectOtherCompanyForm(object_id, request.GET or None)

        if request.GET and form.is_valid():
            # The next page is still to be implemented, redirect to the change list for now
            changelist_route_name = admin_urlname(self.model._meta, 'changelist')
            changelist_url = reverse(changelist_route_name)
            return HttpResponseRedirect(changelist_url)

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': title,
            'form': form,
            'media': self.media,
            'object': obj,
        }
        return TemplateResponse(request, template_name, context)
