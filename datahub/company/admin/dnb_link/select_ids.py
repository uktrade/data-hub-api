from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.admin.dnb_link.forms import SelectIdsToLinkForm
from datahub.core.utils import reverse_with_query_string


@method_decorator(csrf_protect)
def dnb_link_select_ids(model_admin, request):
    """
    View to select Data Hub company id and D&B duns number for linking records.
    Valid POSTs redirect to the change review page.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied()

    is_post = request.method == 'POST'
    data = request.POST if is_post else None
    form = SelectIdsToLinkForm(data=data)

    if is_post and form.is_valid():
        review_changes_route_name = admin_urlname(
            model_admin.model._meta,
            'dnb-link-review-changes',
        )
        review_changes_query_args = {
            'company': form.cleaned_data['company'].pk,
            'duns_number': form.cleaned_data['duns_number'],
        }
        review_changes_url = reverse_with_query_string(
            review_changes_route_name,
            review_changes_query_args,
        )
        return HttpResponseRedirect(review_changes_url)

    template_name = 'admin/company/company/dnb_link/step_1_select_ids.html'
    title = gettext_lazy('Link Company with D&B')

    context = {
        **model_admin.admin_site.each_context(request),
        'opts': model_admin.model._meta,
        'title': title,
        'form': form,
        'media': model_admin.media,
    }
    return TemplateResponse(request, template_name, context)
