import logging

import reversion
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now
from requests.exceptions import ConnectionError, Timeout
from rest_framework import serializers, status
from reversion.models import Version

from datahub.core import statsd
from datahub.core.api_client import APIClient, TokenAuth
from datahub.core.exceptions import APIBadGatewayException
from datahub.core.serializers import AddressSerializer
from datahub.dnb_api.constants import (
    ALL_DNB_UPDATED_MODEL_FIELDS,
    ALL_DNB_UPDATED_SERIALIZER_FIELDS,
    NEW_DNB_SEARCH_FEATURE_FLAG,
)
from datahub.dnb_api.serializers import DNBCompanySerializer
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.metadata.models import AdministrativeArea, Country

logger = logging.getLogger(__name__)


class DNBServiceException(Exception):
    """
    Base exception class for DNBService related errors.
    """


class DNBServiceError(DNBServiceException):
    """
    Exception for when DNB service doesn't return a response with a status code of 200.
    """

    def __init__(self, message, status_code):
        """
        Initialise the exception.
        """
        super().__init__(message)
        self.status_code = status_code


class DNBServiceInvalidRequest(DNBServiceException):
    """
    Exception for when the request to DNB service is not valid.
    """


class DNBServiceInvalidResponse(DNBServiceException):
    """
    Exception for when the response from DNB service is not valid.
    """


class DNBServiceConnectionError(DNBServiceException):
    """
    Exception for when an error was encountered when connecting to DNB service.
    """


class DNBServiceTimeoutError(DNBServiceException):
    """
    Exception for when a timeout was encountered when connecting to DNB service.
    """


class RevisionNotFoundError(Exception):
    """
    Exception for when a revision with the specified comment is not found.
    """


def search_dnb(query_params, request=None):
    """
    Queries the dnb-service with the given query_params. E.g.:

        {"duns_number": "29393217", "page_size": 1}
        {"search_term": "brompton", "page_size": 10}
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    api_client = _get_api_client(request)

    if is_feature_flag_active(NEW_DNB_SEARCH_FEATURE_FLAG):
        response = api_client.request(
            'POST',
            'v2/companies/search/',
            json=query_params,
            timeout=3.0,
        )
    else:
        response = api_client.request(
            'POST',
            'companies/search/',
            json=query_params,
            timeout=3.0,
        )

    statsd.incr(f'dnb.search.{response.status_code}')
    return response


def get_company(duns_number, request=None):
    """
    Pull data for the company with the given duns_number from DNB and
    returns a dict formatted for use with serializer of type CompanySerializer.

    Raises exceptions if the company is not found, if multiple companies are
    found or if the `duns_number` for the company is not the same as the one
    we searched for.
    """
    try:
        dnb_response = search_dnb({'duns_number': duns_number})
    except APIBadGatewayException as exc:
        error_message = 'DNB service unavailable'
        logger.error(error_message)
        raise DNBServiceConnectionError(error_message) from exc
    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        logger.error(error_message)
        raise DNBServiceTimeoutError(error_message) from exc

    if dnb_response.status_code != status.HTTP_200_OK:
        error_message = f'DNB service returned an error status: {dnb_response.status_code}'
        logger.error(error_message)
        raise DNBServiceError(error_message, dnb_response.status_code)

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


def extract_address_from_dnb_company(dnb_company, prefix, ignore_when_missing=()):
    """
    Extract address from dnb company data.  This takes a `prefix` string to
    extract address fields that start with a certain prefix.
    """
    country = Country.objects.filter(
        iso_alpha2_code=dnb_company[f'{prefix}_country'],
    ).first() if dnb_company.get(f'{prefix}_country') else None
    area = AdministrativeArea.objects.filter(
        area_code=dnb_company[f'{prefix}_area_abbrev_name'],
    ).first() if dnb_company.get(f'{prefix}_area_abbrev_name') else None

    extracted_address = {
        'line_1': dnb_company.get(f'{prefix}_line_1') or '',
        'line_2': dnb_company.get(f'{prefix}_line_2') or '',
        'town': dnb_company.get(f'{prefix}_town') or '',
        'county': dnb_company.get(f'{prefix}_county') or '',
        'postcode': dnb_company.get(f'{prefix}_postcode') or '',
        'country': country.id if country else None,
        'area': area.id if area else None,
    }

    for field in ignore_when_missing:
        if not extracted_address[field]:
            return None

    return extracted_address


def format_dnb_company(dnb_company):
    """
    Format DNB response to something that our Serializer
    can work with.
    """
    # Extract companies house number for UK Companies
    registration_numbers = {
        reg['registration_type']: reg.get('registration_number')
        for reg in dnb_company.get('registration_numbers') or []
    }

    domain = dnb_company.get('domain')
    company_website = f'http://{domain}' if domain else ''

    duns_number = dnb_company.get('duns_number')
    turnover_currency = dnb_company.get('annual_sales_currency')

    if turnover_currency and turnover_currency != 'USD':
        logger.error(
            'D&B did not have USD turnover',
            extra={
                'duns_number': duns_number,
                'currency': turnover_currency,
            },
        )
        dnb_company.pop('annual_sales', None)
        dnb_company.pop('is_annual_sales_estimated', None)

    return {
        'name': dnb_company.get('primary_name'),
        'trading_names': dnb_company.get('trading_names'),
        'duns_number': duns_number,
        'address': extract_address_from_dnb_company(dnb_company, 'address'),
        'registered_address': extract_address_from_dnb_company(
            dnb_company,
            'registered_address',
            ignore_when_missing=AddressSerializer.REQUIRED_FIELDS,
        ),
        'uk_based': dnb_company.get('address_country') == 'GB',
        'company_number': registration_numbers.get('uk_companies_house_number'),
        # Optional fields
        'number_of_employees': dnb_company.get('employee_number'),
        'is_number_of_employees_estimated': dnb_company.get('is_employees_number_estimated'),
        'turnover': dnb_company.get('annual_sales'),
        'is_turnover_estimated': dnb_company.get('is_annual_sales_estimated'),
        'website': company_website,
        # `Company.global_ultimate_duns_number` is not nullable but allows blank values. Sample
        # response from the D&B search API suggests that this field can be set to null.
        'global_ultimate_duns_number': dnb_company.get('global_ultimate_duns_number') or '',
        # TODO: Extract sensible values for the following fields form the data:
        # 'business_type': None,
        # 'description': None,
        # 'uk_region': None,
        # 'sector': None,
        # 'vat_number': None,
    }


def update_company_from_dnb(
    dh_company,
    dnb_company,
    user=None,
    fields_to_update=None,
    update_descriptor='',
):
    """
    Updates `dh_company` with new data from `dnb_company` while setting `modified_by` to the
    given user (if specified) and creating a revision.
    If `fields_to_update` is specified, only the fields specified will be synced
    with DNB.  `fields_to_update` should be an iterable of strings representing
    DNBCompanySerializer field names.
    If `update_descriptor` is specified, the descriptor will be injected in to
    the comment for this revision.

    Raises serializers.ValidationError if data is invalid.
    """
    fields_to_update = fields_to_update or ALL_DNB_UPDATED_SERIALIZER_FIELDS
    # Set dnb_company data to only include the fields in fields_to_update
    dnb_company = {field: dnb_company[field] for field in fields_to_update}

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
        company_kwargs = {
            'pending_dnb_investigation': False,
            'dnb_modified_on': now(),
        }
        if user:
            company_kwargs['modified_by'] = user
            reversion.set_user(user)
            company_serializer.save(**company_kwargs)
        else:
            # Call a method to update the fields changed on the serializer only; this prevents
            # us from modifying modified_on - which should only be set through saves initiated by
            # a user
            company_serializer.partial_save(**company_kwargs)

        update_comment = 'Updated from D&B'
        if update_descriptor:
            update_comment = f'{update_comment} [{update_descriptor}]'
        reversion.set_comment(update_comment)


def get_company_update_page(last_updated_after, next_page=None, request=None):
    """
    Get the given company updates page from the dnb-service.

    The request to the dnb-service would look like:

        GET /companies?last_updated_after=2019-11-11T12:00:00&cursor=3465723323

    Where:

        last_updated_after: datetime filter that ensures that only companies
        updated after the given datetime are returned.

        cursor: dnb-service users DRF's CursorPagination for this paginated list
        and cursor is a encoded string that identifies a given page.
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    request_kwargs = {'timeout': 3.0}
    url = next_page
    if not next_page:
        request_kwargs['params'] = {
            'last_updated_after': last_updated_after,
        }
        url = 'companies/'

    try:
        api_client = _get_api_client(request)
        response = api_client.request(
            'GET',
            url,
            **request_kwargs,
        )
    except APIBadGatewayException as exc:
        error_message = 'DNB service unavailable'
        logger.error(error_message)
        raise DNBServiceConnectionError(error_message) from exc
    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        logger.error(error_message)
        raise DNBServiceTimeoutError(error_message) from exc

    if response.status_code != status.HTTP_200_OK:
        error_message = f'DNB service returned an error status: {response.status_code}'
        logger.error(error_message)
        raise DNBServiceError(error_message, response.status_code)

    return response.json()


def _get_rollback_version(company, update_comment):
    versions = Version.objects.get_for_object(company)
    for i, version in enumerate(versions):
        if version.revision.comment == update_comment:
            if (i + 1) < len(versions):
                return versions[i + 1]
            raise RevisionNotFoundError(
                f'Revision with comment: {update_comment} is the base version.',
            )
    raise RevisionNotFoundError(
        f'Revision with comment: {update_comment} not found.',
    )


def rollback_dnb_company_update(
    company,
    update_descriptor,
    fields_to_update=None,
):
    """
    Given a company, an update descriptor that identifies a particular update
    patch and fields that default to ALL_DNB_UPDATE_FIELDS, rollback the record
    to the state before the update was applied.
    """
    fields_to_update = fields_to_update or ALL_DNB_UPDATED_MODEL_FIELDS
    update_comment = f'Updated from D&B [{update_descriptor}]'
    rollback_version = _get_rollback_version(company, update_comment)
    fields = {
        name: value
        for name, value in rollback_version.field_dict.items()
        if name in fields_to_update
    }
    with reversion.create_revision():
        reversion.set_comment(f'Reverted D&B update from: {update_descriptor}')
        for field, value in fields.items():
            setattr(company, field, value)
        company.save(update_fields=fields)


def _request_changes(payload, request=None):
    """
    Submit change request to dnb-service.
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    api_client = _get_api_client(request)
    response = api_client.request(
        'POST',
        'change-request/',
        json=payload,
        timeout=3.0,
    )
    return response


def request_changes(duns_number, changes, request=None):
    """
    Submit change request for the company with the given duns_number
    and changes to the dnb-service.
    """
    try:
        dnb_response = _request_changes(
            {
                'duns_number': duns_number,
                'changes': changes,
            },
            request=request,
        )
    except APIBadGatewayException as exc:
        error_message = 'DNB service unavailable'
        raise DNBServiceConnectionError(error_message) from exc

    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        raise DNBServiceTimeoutError(error_message) from exc

    if not dnb_response.ok:
        error_message = f'DNB service returned an error status: {dnb_response.status_code}'
        raise DNBServiceError(error_message, dnb_response.status_code)

    return dnb_response.json()


def _get_change_request(params, request=None):
    """
    Get change request from dnb-service.
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')
    api_client = _get_api_client(request)
    response = api_client.request(
        'GET',
        'change-request/',
        params=params,
        timeout=3.0,
    )
    return response


def get_change_request(duns_number, status, request=None):
    """
    Get a change request for the company with the given duns_number
    and status from the dnb-service.
    """
    try:
        dnb_response = _get_change_request(
            {
                'duns_number': duns_number,
                'status': status,
            },
            request,
        )

    except ConnectionError as exc:
        error_message = 'Encountered an error connecting to DNB service'
        raise DNBServiceConnectionError(error_message) from exc

    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        raise DNBServiceTimeoutError(error_message) from exc

    if not dnb_response.ok:
        error_message = f'DNB service returned an error status: {dnb_response.status_code}'
        raise DNBServiceError(error_message, dnb_response.status_code)

    return dnb_response.json()


def _create_investigation(payload, request=None):
    """
    Submit change request to dnb-service.
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    api_client = _get_api_client(request)
    response = api_client.request(
        'POST',
        'investigation/',
        json=payload,
        timeout=3.0,
    )
    return response


def create_investigation(investigation_data, request=None):
    """
    Submit change request for the company with the given duns_number
    and changes to the dnb-service.
    """
    try:
        dnb_response = _create_investigation(investigation_data, request)

    except ConnectionError as exc:
        error_message = 'Encountered an error connecting to DNB service'
        raise DNBServiceConnectionError(error_message) from exc

    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        raise DNBServiceTimeoutError(error_message) from exc

    if not dnb_response.ok:
        error_message = f'DNB service returned an error status: {dnb_response.status_code}'
        raise DNBServiceError(error_message, dnb_response.status_code)

    return dnb_response.json()


def _get_api_client(request=None):
    return APIClient(
        settings.DNB_SERVICE_BASE_URL,
        TokenAuth(settings.DNB_SERVICE_TOKEN),
        raise_for_status=False,
        default_timeout=settings.DNB_SERVICE_TIMEOUT,
        request=request,
    )
