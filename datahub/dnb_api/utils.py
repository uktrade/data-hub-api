import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework import status

from datahub.core import statsd
from datahub.core.api_client import APIClient, TokenAuth
from datahub.metadata.models import Country


logger = logging.getLogger(__name__)

api_client = APIClient(
    settings.DNB_SERVICE_BASE_URL,
    TokenAuth(settings.DNB_SERVICE_TOKEN),
    raise_for_status=False,
    default_timeout=settings.DNB_SERVICE_TIMEOUT,
)


class DNBServiceError(Exception):
    """
    Exception for when DNB service doesn't return
    a response with a status code of 200.
    """


class DNBServiceInvalidRequest(Exception):
    """
    Exception for when the request to DNB service
    is not valid.
    """


class DNBServiceInvalidResponse(Exception):
    """
    Exception for when the response from DNB service
    is not valid.
    """


def search_dnb(query_params):
    """
    Queries the dnb-service with the given query_params. E.g.:

        {"duns_number": "29393217", "page_size": 1}
        {"search_term": "brompton", "page_size": 10}
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')
    response = api_client.request(
        'POST',
        'companies/search/',
        json=query_params,
    )
    statsd.incr(f'dnb.search.{response.status_code}')
    return response


def get_company(duns_number):
    """
    Pull data for the company with the given duns_number from DNB and
    returns a dict formatted for use with serializer of type CompanySerializer.

    Raises exceptions if the company is not found, if multiple companies are
    found or if the `duns_number` for the company is not the same as the one
    we searched for.
    """
    dnb_response = search_dnb({'duns_number': duns_number})

    if dnb_response.status_code != status.HTTP_200_OK:
        error_message = f'DNB service returned: {dnb_response.status_code}'
        logger.error(error_message)
        raise DNBServiceError(error_message)

    dnb_companies = dnb_response.json().get('results', [])

    if not dnb_companies:
        error_message = f'Cannot find a company with duns_number: {duns_number}'
        logger.error(error_message)
        raise DNBServiceInvalidRequest(error_message)

    if len(dnb_companies) > 1:
        error_message = f'Multiple companies found with duns_number: {duns_number}'
        logger.error(error_message)
        raise DNBServiceInvalidResponse(error_message)

    dnb_company = dnb_companies[0]

    if dnb_company.get('duns_number') != duns_number:
        error_message = (
            f'DUNS number of the company: {dnb_company.get("duns_number")} '
            f'did not match searched DUNS number: {duns_number}'
        )
        logger.error(error_message)
        raise DNBServiceInvalidResponse(error_message)

    return format_dnb_company(dnb_companies[0])


def format_dnb_company(dnb_company):
    """
    Format DNB response to something that our Serializer
    can work with.
    """
    # Extract country
    country = Country.objects.filter(
        iso_alpha2_code=dnb_company.get('address_country'),
    ).first()

    # Extract companies house number for UK Companies
    registration_numbers = {
        reg['registration_type']: reg.get('registration_number')
        for reg in dnb_company['registration_numbers']
    }

    domain = dnb_company.get('domain')
    company_website = f'http://{domain}' if domain else ''

    return {
        'name': dnb_company.get('primary_name'),
        'trading_names': dnb_company.get('trading_names'),
        'duns_number': dnb_company.get('duns_number'),
        'address': {
            'line_1': dnb_company.get('address_line_1'),
            'line_2': dnb_company.get('address_line_2'),
            'town': dnb_company.get('address_town'),
            'county': dnb_company.get('address_county'),
            'postcode': dnb_company.get('address_postcode'),
            'country': {
                'id': None if country is None else country.id,
            },
        },
        'uk_based': dnb_company.get('address_country') == 'GB',
        'company_number': registration_numbers.get('uk_companies_house_number'),
        # Optional fields
        'number_of_employees': dnb_company.get('employee_number'),
        'is_number_of_employees_estimated': dnb_company.get('is_employees_number_estimated'),
        'turnover': dnb_company.get('annual_sales'),
        'is_turnover_estimated': dnb_company.get('is_annual_sales_estimated'),
        'website': company_website,
        # TODO: Extract sensible values for the following fields form the data:
        # 'business_type': None,
        # 'description': None,
        # 'uk_region': None,
        # 'sector': None,
        # 'vat_number': None,
        # 'global_headquarters': None,
        # 'headquarter_type': None,
    }


def format_dnb_company_investigation(data):
    """
    Format DNB company investigation payload to something
    DNBCompanyInvestigationSerlizer can parse.
    """
    data['dnb_investigation_data'] = {
        'telephone_number': data.pop('telephone_number', None),
    }
    return data
