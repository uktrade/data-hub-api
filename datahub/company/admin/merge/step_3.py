import django.contrib.messages as django_messages
import reversion
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
from datahub.company.models import Contact
from datahub.core.templatetags.datahub_extras import verbose_name_for_count
from datahub.feature_flag.utils import feature_flagged_view
from datahub.interaction.models import Interaction


REVERSION_REVISION_COMMENT = 'Company marked as a duplicate and related records transferred.'
MERGE_SUCCESS_MSG = gettext_lazy(
    'Merge complete – {num_interactions_moved} {interaction_verbose_name}'
    ' and {num_contacts_moved} {contact_verbose_name} moved.',
)
MERGE_FAILURE_MSG = gettext_lazy(
    'Merging failed – merging {source_company} into {target_company} is not allowed.',
)


@feature_flagged_view(MERGE_COMPANY_TOOL_FEATURE_FLAG)
@method_decorator(csrf_protect)
def confirm_merge(model_admin, request):
    """
    View for confirming the merge before it is actually performed.

    This view displays the changes that would be made if the merge proceeds, and asks
    the user to confirm if they want to go ahead.

    Note that the source and target companies are passed in via the query string.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    target_company = model_admin.get_object(request, request.GET.get('target_company'))
    source_company = model_admin.get_object(request, request.GET.get('source_company'))

    if not (source_company and target_company):
        raise SuspiciousOperation()

    is_post = request.method == 'POST'
    merger = DuplicateCompanyMerger(source_company, target_company)

    if is_post and _perform_merge(request, merger, model_admin):
        changelist_route_name = admin_urlname(model_admin.model._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)
        return HttpResponseRedirect(changelist_url)

    template_name = 'admin/company/company/merge/step_3_confirm_selection.html'
    title = gettext_lazy('Confirm merge')

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


def _perform_merge(request, merger, model_admin):
    if not merger.is_valid():
        failure_msg = MERGE_FAILURE_MSG.format(
            source_company=merger.source_company,
            target_company=merger.target_company,
        )
        model_admin.message_user(request, failure_msg, django_messages.ERROR)
        return False

    reversion.set_comment(REVERSION_REVISION_COMMENT)

    merge_result = merger.perform_merge(request.user)
    success_msg = _build_success_msg(merge_result)
    model_admin.message_user(request, success_msg, django_messages.SUCCESS)
    return True


def _build_success_msg(merge_result):
    interaction_verbose_name = verbose_name_for_count(
        merge_result.num_interactions_moved,
        Interaction._meta,
    )
    contact_verbose_name = verbose_name_for_count(merge_result.num_contacts_moved, Contact._meta)
    return MERGE_SUCCESS_MSG.format(
        num_interactions_moved=merge_result.num_interactions_moved,
        num_contacts_moved=merge_result.num_contacts_moved,
        interaction_verbose_name=interaction_verbose_name,
        contact_verbose_name=contact_verbose_name,
    )
