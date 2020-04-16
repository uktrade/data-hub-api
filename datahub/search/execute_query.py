from logging import getLogger

from django.conf import settings

from datahub.core.utils import log_to_sentry


logger = getLogger(__name__)


def execute_search_query(query):
    """
    Executes an Elasticsearch query using the globally configured request timeout.

    (A warning is also logged if the query takes longer than a set threshold.)
    """
    response = query.params(request_timeout=settings.ES_SEARCH_REQUEST_TIMEOUT).execute()

    if response.took >= settings.ES_SEARCH_REQUEST_WARNING_THRESHOLD * 1000:
        logger.warning(f'Elasticsearch query took a long time ({response.took/1000:.2f} seconds)')

        log_data = {
            'query': query.to_dict(),
            'took': response.took,
            'timed_out': response.timed_out,
        }
        log_to_sentry('Elasticsearch query took a long time', extra=log_data)

    return response
