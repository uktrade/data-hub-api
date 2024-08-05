import time

from logging import getLogger

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests.exceptions import HTTPError, Timeout

from datahub.core.api_client import APIClient, HawkAuth
from datahub.core.exceptions import APIBadGatewayException


logger = getLogger(__name__)


class ExportWinsAPIError(Exception):
    """
    Base exception class for Export Wins API related errors.
    """


class ExportWinsAPIHTTPError(ExportWinsAPIError):
    """
    Exception for all HTTP errors.
    """


class ExportWinsAPITimeoutError(ExportWinsAPIError):
    """
    Exception for when a timeout was encountered when connecting to Export Wins API.
    """


class ExportWinsAPIConnectionError(ExportWinsAPIError):
    """
    Exception for when an error was encountered when connecting to Export Wins API.
    """


def _fetch_page(api_client, source_url, max_retries=5, retry_delay=2):
    """
    Requests a page from given relative source_url.
    """
    for attempt in range(max_retries):
        try:
            page = api_client.request('GET', source_url).json()
            break
        except (APIBadGatewayException, Timeout, HTTPError):
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise
    return page['results'], page['next']


def get_legacy_export_wins_dataset(start_url):
    if not all(
        [
            settings.EXPORT_WINS_SERVICE_BASE_URL,
            settings.EXPORT_WINS_HAWK_ID,
            settings.EXPORT_WINS_HAWK_KEY,
        ],
    ):
        raise ImproperlyConfigured('The all EXPORT_WINS_SERVICE* setting must be set')

    api_client = APIClient(
        api_url=settings.EXPORT_WINS_SERVICE_BASE_URL,
        auth=HawkAuth(settings.EXPORT_WINS_HAWK_ID, settings.EXPORT_WINS_HAWK_KEY),
        raise_for_status=True,
        default_timeout=settings.DEFAULT_SERVICE_TIMEOUT,
    )

    source_url = start_url
    items = 0

    try:
        while True:
            results, next_url = _fetch_page(api_client, source_url)

            yield results

            items += len(results)

            if not next_url or 'source=E' in next_url:
                break

            source_url = next_url.replace(
                settings.EXPORT_WINS_SERVICE_BASE_URL,
                '',
            )

    except APIBadGatewayException as exc:
        error_message = 'Export Wins API service unavailable'
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

    logger.info(f'Legacy Export wins dataset {start_url} processed ({items} records).')
