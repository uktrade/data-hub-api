from datahub.search.query_builder import build_autocomplete_query


def execute_autocomplete_query(es_model, keyword_search, limit, only_return_fields=None):
    """Executes the query for autocomplete search returning all suggested documents."""
    autocomplete_search = build_autocomplete_query(
        es_model, keyword_search, limit, only_return_fields,
    )

    results = autocomplete_search.execute()
    return results.suggest.autocomplete[0].options
