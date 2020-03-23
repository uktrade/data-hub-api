from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests.exceptions import ConnectionError, HTTPError, Timeout

from datahub.company.company_matching_api import match_company
from datahub.core.api_client import APIClient, HawkAuth

api_client = APIClient(
    settings.EXPORT_WINS_SERVICE_BASE_URL,
    HawkAuth(settings.EXPORT_WINS_HAWK_ID, settings.EXPORT_WINS_HAWK_KEY),
    raise_for_status=True,
)


class NoMatchIdException(Exception):
    """
    Base exception class for Export Wins API related errors.
    """


class ExportWinsAPIException(Exception):
    """
    Base exception class for Export Wins API related errors.
    """


class ExportWinsAPIHTTPError(Exception):
    """
    Base exception class for Export Wins API related errors.
    """


class ExportWinsAPITimeoutError(ExportWinsAPIException):
    """
    Exception for when a timeout was encountered when connecting to Export Wins API.
    """


class ExportWinsAPIConnectionError(ExportWinsAPIException):
    """
    Exception for when an error was encountered when connecting to Export Wins API.
    """


def get_export_wins(match_id):
    """
    Queries the Export Wins API with the given match id.
    """
    if not all([
        settings.EXPORT_WINS_SERVICE_BASE_URL,
        settings.EXPORT_WINS_HAWK_ID,
        settings.EXPORT_WINS_HAWK_KEY,
    ]):
        raise ImproperlyConfigured('The all COMPANY_MATCHING_SERVICE_* setting must be set')

    response = api_client.request(
        'GET',
        f'wins/match/{match_id}/',
        timeout=3.0,
    )
    return response


def export_wins(company):
    """
    Get all export wins for a given company.
    Returns None when company matching service doesn't return a match id.
    Raises exception an requests.exceptions.HTTPError for status, timeout and a connection error.
    """
    match_id_json = match_company(company).json()
    match_id = match_id_json.get('match_id', None)
    if not match_id:
        raise NoMatchIdException('no match id')

    try:
        response = get_export_wins(match_id)
    except ConnectionError as exc:
        error_message = 'Encountered an error connecting to Export Wins API'
        raise ExportWinsAPIConnectionError(error_message) from exc
    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with Export Wins API'
        raise ExportWinsAPITimeoutError(error_message) from exc
    except HTTPError as exc:
        error_message = (
            'The Export Wins API returned an error status: '
            f'{exc.response.status_code}',
        )
        raise ExportWinsAPIHTTPError(error_message) from exc
    return response
