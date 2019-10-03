import functools
import logging

import reversion
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

from datahub.dnb_api.serializers import DNBCompanySerializer
from datahub.dnb_api.utils import (
    DNBServiceError,
    DNBServiceInvalidRequest,
    DNBServiceInvalidResponse,
    get_company,
)
from datahub.metadata.models import Country


logger = logging.getLogger(__name__)


def _format_company_diff(dh_company, dnb_company):
    """
    Format the Datahub and D&B companies for templates.
    """
    def get_field(name):
        return dh_company._meta.get_field(name)

    return {
        get_field('name'): (
            dh_company.name,
            dnb_company['name'],
        ),
        get_field('address_1'): (
            dh_company.address_1,
            dnb_company['address']['line_1'],
        ),
        get_field('address_2'): (
            dh_company.address_2,
            dnb_company['address']['line_2'],
        ),
        get_field('address_town'): (
            dh_company.address_town,
            dnb_company['address']['town'],
        ),
        get_field('address_county'): (
            dh_company.address_county,
            dnb_company['address']['county'],
        ),
        get_field('address_postcode'): (
            dh_company.address_postcode,
            dnb_company['address']['postcode'],
        ),
        get_field('address_country'): (
            dh_company.address_country,
            Country.objects.get(id=dnb_company['address']['country']),
        ),
        get_field('registered_address_1'): (
            dh_company.registered_address_1,
            dnb_company['registered_address']['line_1'],
        ),
        get_field('registered_address_2'): (
            dh_company.registered_address_2,
            dnb_company['registered_address']['line_2'],
        ),
        get_field('registered_address_town'): (
            dh_company.registered_address_town,
            dnb_company['registered_address']['town'],
        ),
        get_field('registered_address_county'): (
            dh_company.registered_address_county,
            dnb_company['registered_address']['county'],
        ),
        get_field('registered_address_postcode'): (
            dh_company.registered_address_postcode,
            dnb_company['registered_address']['postcode'],
        ),
        get_field('registered_address_country'): (
            dh_company.registered_address_country,
            Country.objects.get(id=dnb_company['registered_address']['country']),
        ),
        get_field('company_number'): (
            dh_company.company_number,
            dnb_company['company_number'],
        ),
        get_field('trading_names'): (
            ', '.join(dh_company.trading_names),
            ', '.join(dnb_company['trading_names']),
        ),
        get_field('website'): (
            dh_company.website,
            dnb_company['website'],
        ),
        get_field('number_of_employees'): (
            dh_company.number_of_employees,
            dnb_company['number_of_employees'],
        ),
        get_field('is_number_of_employees_estimated'): (
            dh_company.is_number_of_employees_estimated,
            dnb_company['is_number_of_employees_estimated'],
        ),
        get_field('turnover'): (
            dh_company.turnover,
            dnb_company['turnover'],
        ),
        get_field('is_turnover_estimated'): (
            dh_company.is_turnover_estimated,
            dnb_company['is_turnover_estimated'],
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


def _update_from_dnb(dh_company, dnb_company, user):
    """
    Updates `dh_company` with `dnb_company` while setting
    `modified_by` to the given user and creating a revision.

    Raises serializers.ValidationError if data is invalid.
    """
    company_serializer = DNBCompanySerializer(
        dh_company,
        data=dnb_company,
        partial=True,
    )

    try:
        company_serializer.is_valid(raise_exception=True)

    except serializers.ValidationError:
        logger.error(
            'Data from D&B did not pass the Data Hub validation checks.',
            extra={'dnb_company': dnb_company, 'errors': company_serializer.errors},
        )
        raise

    with reversion.create_revision():
        company_serializer.save(
            modified_by=user,
            pending_dnb_investigation=False,
        )
        reversion.set_user(user)
        reversion.set_comment('Updated from D&B')


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

    except (DNBServiceError, DNBServiceInvalidResponse):
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
                'diff': _format_company_diff(dh_company, dnb_company),
            },
        )

    try:
        _update_from_dnb(dh_company, dnb_company, request.user)
        return HttpResponseRedirect(company_change_page)
    except serializers.ValidationError:
        message = 'Data from D&B did not pass the Data Hub validation checks.'
        raise AdminException(message, company_change_page)
