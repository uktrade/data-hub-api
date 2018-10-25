from django import forms
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.admin.merge.constants import MERGE_COMPANY_TOOL_FEATURE_FLAG
from datahub.company.merge import DuplicateCompanyMerger
from datahub.company.models import Company
from datahub.feature_flag.utils import feature_flagged_view


class ConfirmMergeStateForm(forms.Form):
    """Form for validating the query string in the confirm merge view."""

    target_company = forms.ModelChoiceField(Company.objects.all())
    source_company = forms.ModelChoiceField(Company.objects.all())


@feature_flagged_view(MERGE_COMPANY_TOOL_FEATURE_FLAG)
@method_decorator(csrf_protect)
def confirm_merge(model_admin, request):
    """
    View for confirming the merge before it is actually performed.

    This view displays the changes that would be made if the merge proceeds, and asks
    the user to confirm if they want to go ahead.

    Note that the source and target companies are passed in via the query string. The
    ConfirmMergeStateForm form is used to validate the query string.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    state_form = ConfirmMergeStateForm(request.GET)

    if not state_form.is_valid():
        raise SuspiciousOperation()

    source_company = state_form.cleaned_data['source_company']
    target_company = state_form.cleaned_data['target_company']
    is_post = request.method == 'POST'

    if is_post:
        # The merging logic is still to be implemented, redirect to the change list for now
        changelist_route_name = admin_urlname(model_admin.model._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)
        return HttpResponseRedirect(changelist_url)

    template_name = 'admin/company/company/merge/step_3_confirm_selection.html'
    title = gettext_lazy('Confirm merge')

    merger = DuplicateCompanyMerger(source_company, target_company)
    move_entries, should_archive_source = merger.get_planned_changes()

    context = {
        **model_admin.admin_site.each_context(request),
        'source_company': source_company,
        'target_company': target_company,
        'move_entries': move_entries,
        'should_archive_source': should_archive_source,
        'media': model_admin.media,
        'opts': model_admin.model._meta,
        'title': title,
    }
    return TemplateResponse(request, template_name, context)
