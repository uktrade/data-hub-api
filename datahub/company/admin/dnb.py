import functools
import logging

from django.contrib import messages
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

from datahub.dnb_api.utils import (
    DNBServiceError,
    DNBServiceInvalidRequest,
    DNBServiceInvalidResponse,
    get_company,
    update_company_from_dnb,
)
from datahub.metadata.models import Country


logger = logging.getLogger(__name__)


def _format_company_diff(dh_company, dnb_company):
    """
    Format the Datahub and D&B companies for templates.
    """
    def get_field(name):
        return dh_company._meta.get_field(name)

    def get_country(address):
        country = address.get('country')
        return None if country is None else Country.objects.get(id=country)

    address = dnb_company.get('address') or {}
    registered_address = dnb_company.get('registered_address') or {}

    return {
        get_field('name'): (
            dh_company.name,
            dnb_company.get('name'),
        ),
        get_field('address_1'): (
            dh_company.address_1,
            address.get('line_1'),
        ),
        get_field('address_2'): (
            dh_company.address_2,
            address.get('line_2'),
        ),
        get_field('address_town'): (
            dh_company.address_town,
            address.get('town'),
        ),
        get_field('address_county'): (
            dh_company.address_county,
            address.get('county'),
        ),
        get_field('address_postcode'): (
            dh_company.address_postcode,
            address.get('postcode'),
        ),
        get_field('address_country'): (
            dh_company.address_country,
            get_country(address),
        ),
        get_field('registered_address_1'): (
            dh_company.registered_address_1,
            registered_address.get('line_1'),
        ),
        get_field('registered_address_2'): (
            dh_company.registered_address_2,
            registered_address.get('line_2'),
        ),
        get_field('registered_address_town'): (
            dh_company.registered_address_town,
            registered_address.get('town'),
        ),
        get_field('registered_address_county'): (
            dh_company.registered_address_county,
            registered_address.get('county'),
        ),
        get_field('registered_address_postcode'): (
            dh_company.registered_address_postcode,
            registered_address.get('postcode'),
        ),
        get_field('registered_address_country'): (
            dh_company.registered_address_country,
            get_country(registered_address),
        ),
        get_field('company_number'): (
            dh_company.company_number,
            dnb_company.get('company_number'),
        ),
        get_field('trading_names'): (
            ', '.join(dh_company.trading_names),
            ', '.join(dnb_company.get('trading_names', [])),
        ),
        get_field('website'): (
            dh_company.website,
            dnb_company.get('website'),
        ),
        get_field('number_of_employees'): (
            dh_company.number_of_employees,
            dnb_company.get('number_of_employees'),
        ),
        get_field('is_number_of_employees_estimated'): (
            dh_company.is_number_of_employees_estimated,
            dnb_company.get('is_number_of_employees_estimated'),
        ),
        get_field('turnover'): (
            dh_company.turnover,
            dnb_company.get('turnover'),
        ),
        get_field('is_turnover_estimated'): (
            dh_company.is_turnover_estimated,
            dnb_company.get('is_turnover_estimated'),
        ),
        get_field('global_ultimate_duns_number'): (
            dh_company.global_ultimate_duns_number,
            dnb_company.get('global_ultimate_duns_number'),
        ),
    }


def redirect_with_message(func):
    """
    Decorator that redirects to a given URL with a given
    message for the user in case of an error.
    """
    @functools.wraps(func)
    def wrapper(model_admin, request, *args, **kwargs):
        try:
            return func(model_admin, request, *args, **kwargs)
        except AdminException as exc:
            message, redirect_url = exc.args
            messages.add_message(request, messages.ERROR, message)
            return HttpResponseRedirect(redirect_url)
    return wrapper


class AdminException(Exception):
    """
    Exception in an admin view. Contains the message
    to be displayed to the usr and the redirect_url.
    """


def handle_dnb_error(func, error_url):
    """
    Call a callable and handle DNB-related errors by transposing them in to
    AdminExceptions.
    """
    try:
        return func()

    except (DNBServiceError, DNBServiceInvalidResponse):
        message = 'Something went wrong in an upstream service.'
        raise AdminException(message, error_url)

    except DNBServiceInvalidRequest:
        message = 'No matching company found in D&B database.'
        raise AdminException(message, error_url)


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

    if request.method == 'GET':
        dnb_company = handle_dnb_error(
            lambda: get_company(dh_company.duns_number),
            company_change_page,
        )

        return TemplateResponse(
            request,
            'admin/company/company/update-from-dnb.html',
            {
                **model_admin.admin_site.each_context(request),
                'media': model_admin.media,
                'opts': model_admin.model._meta,
                'object': dh_company,
                'title': gettext_lazy('Confirm update from D&B'),
                'diff': _format_company_diff(dh_company, dnb_company),
            },
        )

    try:
        handle_dnb_error(
            lambda: update_company_from_dnb(dh_company, user=request.user),
            company_change_page,
        )
        return HttpResponseRedirect(company_change_page)
    except serializers.ValidationError:
        message = 'Data from D&B did not pass the Data Hub validation checks.'
        raise AdminException(message, company_change_page)
