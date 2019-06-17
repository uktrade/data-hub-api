from logging import getLogger

import sentry_sdk
from django.conf import settings

from datahub.search.query_builder import build_autocomplete_query


logger = getLogger(__name__)


def execute_autocomplete_query(es_model, keyword_search, limit, fields_to_include, context):
    """Executes the query for autocomplete search returning all suggested documents."""
    autocomplete_search = build_autocomplete_query(
        es_model,
        keyword_search,
        limit,
        fields_to_include,
        context,
    )

    results = autocomplete_search.execute()
    return results.suggest.autocomplete[0].options


def execute_search_query(query):
    """
    Executes an Elasticsearch query using the globally configured request timeout.

    (A warning is also logged if the query takes longer than a set threshold.)
    """
    response = query.params(request_timeout=settings.ES_SEARCH_REQUEST_TIMEOUT).execute()

    if response.took >= settings.ES_SEARCH_REQUEST_WARNING_THRESHOLD * 1000:
        logger.warning(f'Elasticsearch query took a long time ({response.took/1000:.2f} seconds)')

        with sentry_sdk.push_scope() as scope:
            scope.set_extra('query', query.to_dict())
            scope.set_extra('took', response.took)
            scope.set_extra('timed_out', response.timed_out)

            sentry_sdk.capture_message('Elasticsearch query took a long time')

    return response
