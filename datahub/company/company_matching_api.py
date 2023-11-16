import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now
from requests.exceptions import HTTPError, Timeout

from datahub.company.models import Company
from datahub.core.api_client import APIClient, HawkAuth
from datahub.core.exceptions import APIBadGatewayException

logger = logging.getLogger(__name__)


class CompanyMatchingServiceError(Exception):
    """
    Base exception class for Company matching service related errors.
    """


class CompanyMatchingServiceHTTPError(CompanyMatchingServiceError):
    """
    Exception for when Company matching service returns an http error status.
    """


class CompanyMatchingServiceTimeoutError(CompanyMatchingServiceError):
    """
    Exception for when a timeout was encountered when connecting to Company matching service.
    """


class CompanyMatchingServiceConnectionError(CompanyMatchingServiceError):
    """
    Exception for when an error was encountered when connecting to Company matching service.
    """


def request_match_companies(json_body, request=None):
    """
    Queries the company matching service with the given json_body. E.g.:
    {
        "descriptions": [
            {
                "id": "1",
                "companies_house_id": "0921309",
                "duns_number": "d210"
                "company_name":"apple",
                "contact_email": "john@apple.com",
                "cdms_ref": "782934",
                "postcode": "SW129RP"
            }
        ]
    }

    Note that the ID field typically the company UUID that is returned by the api for data mapping.
    ID and at least one of the following fields companies_house_id, duns_number, company_name,
    contact_email, cdms_ref and postcode are required.
    """
    if not all([
        settings.COMPANY_MATCHING_SERVICE_BASE_URL,
        settings.COMPANY_MATCHING_HAWK_ID,
        settings.COMPANY_MATCHING_HAWK_KEY,
    ]):
        raise ImproperlyConfigured('The all COMPANY_MATCHING_SERVICE_* setting must be set')

    api_client = APIClient(
        api_url=settings.COMPANY_MATCHING_SERVICE_BASE_URL,
        auth=HawkAuth(settings.COMPANY_MATCHING_HAWK_ID,
                      settings.COMPANY_MATCHING_HAWK_KEY),
        raise_for_status=True,
        default_timeout=settings.DEFAULT_SERVICE_TIMEOUT,
        request=request,
    )
    return api_client.request(
        'POST',
        'api/v1/company/match/',
        json=json_body,
        timeout=3.0,
    )


def _format_company_for_post(companies):
    """Format the Company model to json for the POST body."""
    descriptions = [
        {
            'id': str(company.id),
            'company_name': company.name,
            'companies_house_id': company.company_number,
            'duns_number': company.duns_number,
            'postcode': company.address_postcode,
            'cdms_ref': company.reference_code,
        }
        for company in companies
    ]

    return {
        'descriptions': [
            {
                key: value
                for key, value in description.items() if value
            }
            for description in descriptions
        ],
    }


def match_company(companies, request=None):
    """
    Get match id for all Company objects and return response from the company
    matching service.
    Raises exception an requests.exceptions.HTTPError for status, timeout and a connection error.
    """
    try:
        response = request_match_companies(
            _format_company_for_post(companies),
            request,
        )
    except APIBadGatewayException as exc:
        logger.error(exc)
        error_message = 'Encountered an error connecting to Company matching service'
        raise CompanyMatchingServiceConnectionError(error_message) from exc
    except Timeout as exc:
        logger.error(exc)
        error_message = 'Encountered a timeout interacting with Company matching service'
        raise CompanyMatchingServiceTimeoutError(error_message) from exc
    except HTTPError as exc:
        logger.error(exc)
        error_message = (
            'The Company matching service returned an error status: '
            f'{exc.response.status_code}',
        )
        raise CompanyMatchingServiceHTTPError(error_message) from exc
    return response


def extract_match_ids(response_json):
    """
    Extracts match id out of company matching response.
    {
        'matches': [
            {
                'id': '',
                'match_id': 1234,
                'similarity': '100000'
            },
        ]
    }
    """
    match_ids = [match['match_id'] for match in response_json if match.get('match_id', None)]
    return match_ids


def bulk_match_not_matched_companies(length=100):
    """Match companies using Company Matching service and store closest match_id."""
    companies = Company.objects.filter(export_win_last_matched_on__isnull=True)

    for company in companies[:length]:
        companies_to_match = [company]
        for transferred_from_company in company.transferred_from.all():
            companies_to_match.append(transferred_from_company)
        matching_response = match_company(companies_to_match)
        match_ids = extract_match_ids(matching_response.json().get('matches', []))
        to_update = {}
        if len(match_ids):
            to_update['export_win_match_id'] = match_ids[0]
        to_update['export_win_last_matched_on'] = now()
        # using update to avoid triggering OpenSearch synchronisation
        Company.objects.filter(id=company.pk).update(**to_update)
