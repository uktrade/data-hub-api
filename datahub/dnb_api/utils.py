from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from datahub.core.api_client import APIClient, TokenAuth
from datahub.metadata.models import Country


api_client = APIClient(
    settings.DNB_SERVICE_BASE_URL,
    TokenAuth(settings.DNB_SERVICE_TOKEN),
    raise_for_status=False,
    default_timeout=settings.DNB_SERVICE_TIMEOUT,
)


def search_dnb(query_params):
    """
    Queries the dnb-service with the given query_params. E.g.:

        {"duns_number": "29393217", "page_size": 1}
        {"search_term": "brompton", "page_size": 10}
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')
    return api_client.request(
        'POST',
        'companies/search/',
        json=query_params,
    )


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
        'website': f'http://{dnb_company.get("domain")}',
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
