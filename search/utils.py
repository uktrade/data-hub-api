from elasticsearch_dsl import Search


def search_companies(client, index, term):
    search = Search(using=client, index=index).query('query_string', query=term)
    results = search.execute()
