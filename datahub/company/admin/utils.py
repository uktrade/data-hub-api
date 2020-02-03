import functools

from django.contrib import messages
from django.http import HttpResponseRedirect

from datahub.metadata.models import Country


def format_company_diff(dh_company, dnb_company):
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
