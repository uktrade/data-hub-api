from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.http import HttpResponseRedirect
from django.urls import reverse


def dnb_link_review_changes(model_admin, request):
    """
    View to allow users to review changes that would be applied to a record before linking it.
    POSTs make the link and redirect the user to view the updated record.
    """
    # TODO: Remove this temporary redirect
    company_change_url = reverse(
        admin_urlname(model_admin.model._meta, 'changelist'),
    )
    return HttpResponseRedirect(company_change_url)
