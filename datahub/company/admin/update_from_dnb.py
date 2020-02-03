import logging

from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from rest_framework import serializers

from datahub.company.admin.utils import (
    AdminException,
    format_company_diff,
    redirect_with_message,
)
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceInvalidRequest,
    DNBServiceInvalidResponse,
    DNBServiceTimeoutError,
    get_company,
    update_company_from_dnb,
)


logger = logging.getLogger(__name__)


@redirect_with_message
@method_decorator(require_http_methods(['GET', 'POST']))
@method_decorator(csrf_protect)
def update_from_dnb(model_admin, request, object_id):
    """
    Tool to let admin users update company with a valid `duns_number`
    by pulling fresh data from D&B.

    The company record will be versioned after the update from
    D&B is applied.

    The `pending_dnb_investigation` field will
    be set to False.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied()

    dh_company = model_admin.get_object(request, object_id)

    company_change_page = reverse(
        admin_urlname(model_admin.model._meta, 'change'),
        kwargs={'object_id': dh_company.pk},
    )

    if dh_company is None or dh_company.duns_number is None:
        raise SuspiciousOperation()

    try:
        dnb_company = get_company(dh_company.duns_number)

    except (
        DNBServiceError,
        DNBServiceConnectionError,
        DNBServiceTimeoutError,
        DNBServiceInvalidResponse,
    ):
        message = 'Something went wrong in an upstream service.'
        raise AdminException(message, company_change_page)

    except DNBServiceInvalidRequest:
        message = 'No matching company found in D&B database.'
        raise AdminException(message, company_change_page)

    if request.method == 'GET':
        return TemplateResponse(
            request,
            'admin/company/company/update-from-dnb.html',
            {
                **model_admin.admin_site.each_context(request),
                'media': model_admin.media,
                'opts': model_admin.model._meta,
                'object': dh_company,
                'title': gettext_lazy('Confirm update from D&B'),
                'diff': format_company_diff(dh_company, dnb_company),
            },
        )

    try:
        update_company_from_dnb(dh_company, dnb_company, request.user)
        return HttpResponseRedirect(company_change_page)
    except serializers.ValidationError:
        message = 'Data from D&B did not pass the Data Hub validation checks.'
        raise AdminException(message, company_change_page)
