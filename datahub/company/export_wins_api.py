from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests.exceptions import ConnectionError, HTTPError, Timeout

from datahub.core.api_client import APIClient, HawkAuth

api_client = APIClient(
    settings.EXPORT_WINS_SERVICE_BASE_URL,
    HawkAuth(settings.EXPORT_WINS_HAWK_ID, settings.EXPORT_WINS_HAWK_KEY),
    raise_for_status=True,
)


class ExportWinsAPIException(Exception):
    """
    Base exception class for Export Wins API related errors.
    """


class ExportWinsAPIHTTPError(ExportWinsAPIException):
    """
    Exception for all HTTP errors.
    """


class ExportWinsAPITimeoutError(ExportWinsAPIException):
    """
    Exception for when a timeout was encountered when connecting to Export Wins API.
    """


class ExportWinsAPIConnectionError(ExportWinsAPIException):
    """
    Exception for when an error was encountered when connecting to Export Wins API.
    """


def fetch_export_wins(match_ids):
    """
    Queries the Export Wins API with the given list of match ids.
    Export Wins API takes either a single match id or comma separated
    list of match ids.
    """
    if not all([
        settings.EXPORT_WINS_SERVICE_BASE_URL,
        settings.EXPORT_WINS_HAWK_ID,
        settings.EXPORT_WINS_HAWK_KEY,
    ]):
        raise ImproperlyConfigured('The all EXPORT_WINS_SERVICE* setting must be set')

    match_ids_str = ','.join(list(map(str, match_ids)))
    response = api_client.request(
        'GET',
        f'wins/match?match_id={match_ids_str}',
        timeout=3.0,
    )
    return response


def get_export_wins(match_ids):
    """
    Get all export wins for all given company match_ids.

    `match_ids` is a list of match ids from Company matchin service.
    Raises exception an requests.exceptions.HTTPError for status, timeout and a connection error.
    """
    try:
        response = fetch_export_wins(match_ids)
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
