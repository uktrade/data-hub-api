from urllib.parse import urlencode

from django import forms
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy

from datahub.company.admin.merge.constants import MERGE_COMPANY_TOOL_FEATURE_FLAG
from datahub.company.models import Company
from datahub.core.admin import RawIdWidget
from datahub.feature_flag.utils import feature_flagged_view


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


@feature_flagged_view(MERGE_COMPANY_TOOL_FEATURE_FLAG)
def merge_select_other_company(model_admin, request, object_id):
    """
    First view as part of the merge duplicate companies process.

    Used to select the second company of the two to merge.

    As this does not modify state, the form is submitted using GET rather than POST.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    template_name = 'admin/company/company/merge_select_other_company.html'
    title = gettext_lazy('Merge with another company')

    obj = model_admin.get_object(request, unquote(object_id))
    form = SelectOtherCompanyForm(object_id, request.GET or None)

    if request.GET and form.is_valid():
        select_primary_route_name = admin_urlname(
            model_admin.model._meta,
            'merge-select-primary-company',
        )
        select_primary_url = reverse(select_primary_route_name)
        select_primary_args = urlencode({
            'company_1': unquote(object_id),
            'company_2': form.cleaned_data['other_company'].pk,
        })
        return HttpResponseRedirect(f'{select_primary_url}?{select_primary_args}')

    context = {
        **model_admin.admin_site.each_context(request),
        'opts': model_admin.model._meta,
        'title': title,
        'form': form,
        'media': model_admin.media,
        'object': obj,
    }
    return TemplateResponse(request, template_name, context)
