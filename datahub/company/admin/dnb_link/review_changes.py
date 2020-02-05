from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers

from datahub.company.admin.dnb_link.forms import SelectIdsToLinkForm
from datahub.company.admin.utils import (
    AdminException,
    format_company_diff,
    redirect_with_message,
)
from datahub.dnb_api.link_company import link_company_with_dnb
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceInvalidRequest,
    DNBServiceInvalidResponse,
    DNBServiceTimeoutError,
    get_company,
)


def _build_error_message(all_errors):
    error_message = ''
    for field, errors in all_errors.items():
        concatenated_errors = ', '.join(errors)
        error_message += f'{field}: {concatenated_errors} '
    return error_message


def _link_company_with_dnb(dh_company_id, duns_number, user, error_url):
    # We don't need to catch CompanyAlreadyDNBLinkedException as our form will
    # do this validation for us
    try:
        link_company_with_dnb(dh_company_id, duns_number, user)
    except serializers.ValidationError:
        message = 'Data from D&B did not pass the Data Hub validation checks.'
        raise AdminException(message, error_url)
    except (
        DNBServiceError,
        DNBServiceConnectionError,
        DNBServiceTimeoutError,
        DNBServiceInvalidResponse,
    ):
        message = 'Something went wrong in an upstream service.'
        raise AdminException(message, error_url)
    except DNBServiceInvalidRequest:
        message = 'No matching company found in D&B database.'
        raise AdminException(message, error_url)


def _get_company(duns_number, error_url):
    try:
        return get_company(duns_number)

    except (
        DNBServiceError,
        DNBServiceConnectionError,
        DNBServiceTimeoutError,
        DNBServiceInvalidResponse,
    ):
        message = 'Something went wrong in an upstream service.'
        raise AdminException(message, error_url)

    except DNBServiceInvalidRequest:
        message = 'No matching company found in D&B database.'
        raise AdminException(message, error_url)


@redirect_with_message
@method_decorator(csrf_protect)
def dnb_link_review_changes(model_admin, request):
    """
    View to allow users to review changes that would be applied to a record before linking it.
    POSTs make the link and redirect the user to view the updated record.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied()

    company_list_page = reverse(
        admin_urlname(model_admin.model._meta, 'changelist'),
    )

    form = SelectIdsToLinkForm(data=request.GET)
    if not form.is_valid():
        message = _build_error_message(form.errors)
        raise AdminException(message, company_list_page)

    dh_company = form.cleaned_data['company']
    duns_number = form.cleaned_data['duns_number']

    is_post = request.method == 'POST'

    if is_post:
        _link_company_with_dnb(dh_company.pk, duns_number, request.user, company_list_page)

        messages.add_message(request, messages.SUCCESS, 'Company linked to D&B successfully.')
        company_change_page = reverse(
            admin_urlname(model_admin.model._meta, 'change'),
            kwargs={'object_id': dh_company.pk},
        )
        return HttpResponseRedirect(company_change_page)

    dnb_company = _get_company(duns_number, company_list_page)

    return TemplateResponse(
        request,
        'admin/company/company/update-from-dnb.html',
        {
            **model_admin.admin_site.each_context(request),
            'media': model_admin.media,
            'opts': model_admin.model._meta,
            'title': gettext_lazy('Confirm Link Company with D&B'),
            'diff': format_company_diff(dh_company, dnb_company),
        },
    )
