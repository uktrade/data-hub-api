from elasticsearch_dsl import Search


def search_by_term(client, index, term, offset=0, limit=100):
    """Use Elasticsearch DSL to perform a query search."""

    search = Search(
        using=client,
        index=index
    ).query(
        'query_string',
        query=term
    )[offset:offset+limit]
    results = search.execute()

    return results
