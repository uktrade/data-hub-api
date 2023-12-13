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
    MergeNotAllowedError,
    transform_merge_results_to_merge_entry_summaries,
)
from datahub.company.merge_company import (
    merge_companies,
    MERGE_CONFIGURATION as COMPANY_MERGE_CONFIGURATION,
)
from datahub.company.merge_contact import (
    MERGE_CONFIGURATION as CONTACT_MERGE_CONFIGURATION,
    merge_contacts,
)

from datahub.core.templatetags.datahub_extras import verbose_name_for_count

COMPANY_REVERSION_REVISION_COMMENT = """
    Company marked as a duplicate and related records transferred.
"""

CONTACT_REVERSION_REVISION_COMMENT = """
    Contact marked as a duplicate and related records transferred.
"""

MERGE_ENTRY_MSG_FRAGMENT = gettext_lazy(
    '{0} {1}{2}',
)
MERGE_SUCCESS_MSG = gettext_lazy(
    'Merge complete – {merge_entries} moved from'
    ' <a href="{source_url}" target="_blank">{source}</a> to'
    ' <a href="{target_url}" target="_blank">{target}</a>.',
)
MERGE_FAILURE_MSG = gettext_lazy(
    'Merging failed – merging {source} into {target} is not allowed.',
)


def confirm_merge_contacts(model_admin, request):
    dict = {
        'merge_fn': merge_contacts,
        'template_name': 'admin/company/contact/merge/step_3_confirm_selection.html',
        'reversion_revision_comment': CONTACT_REVERSION_REVISION_COMMENT,
        'merge_configuration': CONTACT_MERGE_CONFIGURATION,
    }
    return confirm_merge(model_admin, request, dict)


def confirm_merge_companies(model_admin, request):
    dict = {
        'merge_fn': merge_companies,
        'template_name': 'admin/company/company/merge/step_3_confirm_selection.html',
        'reversion_revision_comment': COMPANY_REVERSION_REVISION_COMMENT,
        'merge_configuration': COMPANY_MERGE_CONFIGURATION,
    }
    return confirm_merge(model_admin, request, dict)


@method_decorator(csrf_protect)
def confirm_merge(model_admin, request, dict):
    """
    View for confirming the merge before it is actually performed.

    This view displays the changes that would be made if the merge proceeds, and asks
    the user to confirm if they want to go ahead.

    Note that the source and target records are passed in via the query string.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    target = model_admin.get_object(request, request.GET.get('target'))
    source = model_admin.get_object(request, request.GET.get('source'))

    if not (source and target):
        raise SuspiciousOperation()

    is_post = request.method == 'POST'

    if is_post and _perform_merge(request, source, target, model_admin, dict):
        changelist_route_name = admin_urlname(model_admin.model._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)
        return HttpResponseRedirect(changelist_url)

    title = gettext_lazy('Confirm merge')

    merge_configuration = dict['merge_configuration']
    planned_merge_results, should_archive_source = get_planned_changes(source, merge_configuration)
    merge_entries = transform_merge_results_to_merge_entry_summaries(
        planned_merge_results,
        skip_zeroes=True,
    )

    context = {
        **model_admin.admin_site.each_context(request),
        'source': source,
        'target': target,
        'merge_entries': merge_entries,
        'should_archive_source': should_archive_source,
        'media': model_admin.media,
        'opts': model_admin.model._meta,
        'title': title,
    }
    template_name = dict['template_name']
    return TemplateResponse(request, template_name, context)


def _perform_merge(request, source, target, model_admin, dict):
    try:
        merge_fn = dict['merge_fn']
        merge_results = merge_fn(source, target, request.user)
    except MergeNotAllowedError:
        failure_msg = MERGE_FAILURE_MSG.format(
            source=source,
            target=target,
        )
        model_admin.message_user(request, failure_msg, django_messages.ERROR)
        return False

    reversion_revision_comment = dict['reversion_revision_comment']
    reversion.set_comment(reversion_revision_comment)
    success_msg = _build_success_msg(source, target, merge_results)
    model_admin.message_user(request, success_msg, django_messages.SUCCESS)
    return True


def _build_success_msg(source, target, merge_results):
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
        source_url=source.get_absolute_url(),
        source=source,
        target_url=target.get_absolute_url(),
        target=target,
    )
    return html
