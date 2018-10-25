from django import forms
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.admin.merge.constants import MERGE_COMPANY_TOOL_FEATURE_FLAG
from datahub.company.models import Company
from datahub.core.admin import RawIdWidget
from datahub.core.utils import reverse_with_query_string
from datahub.feature_flag.utils import feature_flagged_view


class SelectOtherCompanyStateForm(forms.Form):
    """Form for validating the query string in the select other company view."""

    company_1 = forms.ModelChoiceField(Company.objects.all())


class SelectOtherCompanyForm(forms.Form):
    """Form used for selecting a second company when merging duplicate companies."""

    BOTH_COMPANIES_ARE_THE_SAME_MSG = gettext_lazy(
        'The two companies to merge cannot be the same. Please select a different company.',
    )

    company_2 = forms.ModelChoiceField(
        Company.objects.all(),
        widget=RawIdWidget(Company),
        label='Other company',
    )

    def __init__(self, company_1, *args, **kwargs):
        """Initialises the form, saving the ID of the company already selected."""
        super().__init__(*args, **kwargs)
        self._company_1 = company_1

    def clean_company_2(self):
        """Checks that a different company than the one navigated from has been selected."""
        company_2 = self.cleaned_data['company_2']
        if company_2 == self._company_1:
            raise ValidationError(self.BOTH_COMPANIES_ARE_THE_SAME_MSG)
        return company_2


@feature_flagged_view(MERGE_COMPANY_TOOL_FEATURE_FLAG)
@method_decorator(csrf_protect)
def merge_select_other_company(model_admin, request):
    """
    First view as part of the merge duplicate companies process.

    Used to select the second company of the two to merge.

    Note that the ID of the first company is passed in via the query string. The query
    string is validated using the SelectOtherCompanyStateForm form.

    SelectOtherCompanyForm the form used to validate the POST body.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    state_form = SelectOtherCompanyStateForm(request.GET)

    if not state_form.is_valid():
        raise SuspiciousOperation()

    company_1 = state_form.cleaned_data['company_1']
    is_post = request.method == 'POST'
    data = request.POST if is_post else None
    form = SelectOtherCompanyForm(company_1, data=data)

    if is_post and form.is_valid():
        select_primary_route_name = admin_urlname(
            model_admin.model._meta,
            'merge-select-primary-company',
        )
        select_primary_query_args = {
            'company_1': company_1.pk,
            'company_2': form.cleaned_data['company_2'].pk,
        }
        select_primary_url = reverse_with_query_string(
            select_primary_route_name,
            select_primary_query_args,
        )
        return HttpResponseRedirect(select_primary_url)

    template_name = 'admin/company/company/merge/step_1_select_other_company.html'
    title = gettext_lazy('Merge with another company')

    context = {
        **model_admin.admin_site.each_context(request),
        'opts': model_admin.model._meta,
        'title': title,
        'form': form,
        'media': model_admin.media,
        'object': company_1,
    }
    return TemplateResponse(request, template_name, context)
