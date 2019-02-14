import django.contrib.messages as django_messages
import reversion
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.merge import (
    get_planned_changes,
    merge_companies,
    MergeNotAllowedError,
    transform_merge_results_to_merge_entry_summaries,
)
from datahub.core.templatetags.datahub_extras import verbose_name_for_count

REVERSION_REVISION_COMMENT = 'Company marked as a duplicate and related records transferred.'
MERGE_ENTRY_MSG_FRAGMENT = gettext_lazy(
    '{0} {1}{2}',
)
MERGE_SUCCESS_MSG = gettext_lazy(
    'Merge complete – {merge_entries} moved from'
    ' <a href="{source_company_url}" target="_blank">{source_company}</a> to'
    ' <a href="{target_company_url}" target="_blank">{target_company}</a>.',
)
MERGE_FAILURE_MSG = gettext_lazy(
    'Merging failed – merging {source_company} into {target_company} is not allowed.',
)


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

    if is_post and _perform_merge(request, source_company, target_company, model_admin):
        changelist_route_name = admin_urlname(model_admin.model._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)
        return HttpResponseRedirect(changelist_url)

    template_name = 'admin/company/company/merge/step_3_confirm_selection.html'
    title = gettext_lazy('Confirm merge')

    planned_merge_results, should_archive_source = get_planned_changes(source_company)
    merge_entries = transform_merge_results_to_merge_entry_summaries(
        planned_merge_results,
        skip_zeroes=True,
    )

    context = {
        **model_admin.admin_site.each_context(request),
        'source_company': source_company,
        'target_company': target_company,
        'merge_entries': merge_entries,
        'should_archive_source': should_archive_source,
        'media': model_admin.media,
        'opts': model_admin.model._meta,
        'title': title,
    }
    return TemplateResponse(request, template_name, context)


def _perform_merge(request, source_company, target_company, model_admin):
    try:
        merge_results = merge_companies(source_company, target_company, request.user)
    except MergeNotAllowedError:
        failure_msg = MERGE_FAILURE_MSG.format(
            source_company=source_company,
            target_company=target_company,
        )
        model_admin.message_user(request, failure_msg, django_messages.ERROR)
        return False

    reversion.set_comment(REVERSION_REVISION_COMMENT)
    success_msg = _build_success_msg(source_company, target_company, merge_results)
    model_admin.message_user(request, success_msg, django_messages.SUCCESS)
    return True


def _build_success_msg(source_company, target_company, merge_results):
    merge_entries = transform_merge_results_to_merge_entry_summaries(
        merge_results,
        skip_zeroes=True,
    )

    messages = (
        (
            merge_entry.count,
            verbose_name_for_count(merge_entry.count, merge_entry.model_meta),
            merge_entry.description,
        ) for merge_entry in merge_entries
    )

    html_merge_entries = format_html_join(', ', MERGE_ENTRY_MSG_FRAGMENT, messages)

    html = format_html(
        MERGE_SUCCESS_MSG,
        merge_entries=html_merge_entries,
        source_company_url=source_company.get_absolute_url(),
        source_company=source_company,
        target_company_url=target_company.get_absolute_url(),
        target_company=target_company,
    )
    return html
