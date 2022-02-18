from logging import getLogger
from urllib.parse import urlparse

from django.conf import settings
from opensearchpy.exceptions import ConnectionError

from datahub.core.exceptions import APIBadGatewayException
from datahub.core.utils import log_to_sentry

logger = getLogger(__name__)


def execute_search_query(query):
    """
    Executes an Elasticsearch query using the globally configured request timeout.

    (A warning is also logged if the query takes longer than a set threshold.)
    """
    try:
        response = query.params(request_timeout=settings.ES_SEARCH_REQUEST_TIMEOUT).execute()
    except ConnectionError:
        raise APIBadGatewayException(
            f'Upstream service unavailable: {urlparse(settings.OPENSEARCH_URL).netloc}',
        )

    if response.took >= settings.ES_SEARCH_REQUEST_WARNING_THRESHOLD * 1000:
        logger.warning(f'Elasticsearch query took a long time ({response.took / 1000:.2f}s)')

        log_data = {
            'query': query.to_dict(),
            'took': response.took,
            'timed_out': response.timed_out,
        }
        log_to_sentry('Elasticsearch query took a long time', extra=log_data)

    return response
