from django import forms
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.admin.merge.constants import MERGE_COMPANY_TOOL_FEATURE_FLAG
from datahub.company.merge import DuplicateCompanyMerger
from datahub.core.utils import reverse_with_query_string
from datahub.feature_flag.utils import feature_flagged_view


class SelectPrimaryCompanyForm(forms.Form):
    """Form used for selecting which company to keep as active after merging companies."""

    INVALID_TARGET_COMPANY_MSG = gettext_lazy(
        'The company selected is archived.',
    )
    INVALID_SOURCE_COMPANY_MSG = gettext_lazy(
        'The other company has related records which can’t be moved to the selected company.',
    )

    selected_company = forms.ChoiceField(
        choices=(
            ('1', 'Company 1'),
            ('2', 'Company 2'),
        ),
        widget=forms.RadioSelect(),
    )

    def __init__(self, company_1, company_2, *args, **kwargs):
        """Saves a reference to the two companies available for selection."""
        super().__init__(*args, **kwargs)

        self._company_1 = company_1
        self._company_2 = company_2

    def clean(self):
        """
        Checks that the selection made is allowed.

        This makes sure that the target company selected is not archived and the source company
        does not have any referencing objects that are not handled during merging (such
        as investment projects or OMIS orders referencing the company).
        """
        cleaned_data = super().clean()
        company_index = cleaned_data.get('selected_company')

        if not company_index:
            return

        target_company = self._company_1 if company_index == '1' else self._company_2
        source_company = self._company_1 if company_index != '1' else self._company_2

        merger = DuplicateCompanyMerger(source_company, target_company)

        if not merger.is_target_valid():
            raise ValidationError(self.INVALID_TARGET_COMPANY_MSG)

        if not merger.is_source_valid():
            raise ValidationError(self.INVALID_SOURCE_COMPANY_MSG)

        cleaned_data['target_company'] = target_company
        cleaned_data['source_company'] = source_company

        return cleaned_data


@feature_flagged_view(MERGE_COMPANY_TOOL_FEATURE_FLAG)
@method_decorator(csrf_protect)
def select_primary_company(model_admin, request):
    """
    View for selecting the company to retain.

    This is the view where the user selects which company should remain as the
    active record and which one should be archived.

    Note that the IDs of the two companies to select from are passed in via the
    query string.

    SelectPrimaryCompanyForm is used to validate the POST body on submission of the form.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    company_1 = model_admin.get_object(request, request.GET.get('company_1'))
    company_2 = model_admin.get_object(request, request.GET.get('company_2'))

    if not (company_1 and company_2):
        raise SuspiciousOperation()

    is_post = request.method == 'POST'
    data = request.POST if is_post else None
    form = SelectPrimaryCompanyForm(company_1, company_2, data=data)

    if is_post and form.is_valid():
        confirm_route_name = admin_urlname(
            model_admin.model._meta,
            'merge-confirm',
        )
        confirm_query_args = {
            'source_company': form.cleaned_data['source_company'].pk,
            'target_company': form.cleaned_data['target_company'].pk,
        }
        confirm_url = reverse_with_query_string(confirm_route_name, confirm_query_args)
        return HttpResponseRedirect(confirm_url)

    template_name = 'admin/company/company/merge/step_2_primary_selection.html'
    title = gettext_lazy('Select which company should be retained')

    context = {
        **model_admin.admin_site.each_context(request),
        'option_1': _build_option_context(company_2, company_1),
        'option_2': _build_option_context(company_1, company_2),
        'form': form,
        'media': model_admin.media,
        'opts': model_admin.model._meta,
        'title': title,
    }
    return TemplateResponse(request, template_name, context)


def _build_option_context(source_company, target_company):
    merger = DuplicateCompanyMerger(source_company, target_company)
    return {
        'target': target_company,
        'is_source_valid': merger.is_source_valid(),
        'is_target_valid': merger.is_target_valid(),
        'is_valid': merger.is_valid(),
    }
