import json
from django.http import HttpResponse
from api.models.searchitem import SearchItem
from datahubapi import settings


def transform_search_result(es_result, term, filters={}):
    result = {
        "term": term,
        "total": es_result["hits"]["total"],
        "max_score": es_result["hits"]["max_score"],
        "hits": es_result["hits"]["hits"],
        "filters": filters
    }

    facets = {}
    aggregations = es_result["aggregations"]

    for aggregation_key, aggregation_value in aggregations.items():
        facets[aggregation_key] = []
        for aggregation_bucket in aggregation_value["buckets"]:
            facets[aggregation_key].append({"value": aggregation_bucket["key"], "total": aggregation_bucket["doc_count"]})

    result["facets"] = facets
    return result


def es_search(term, filters={}):
    query = {
        "query": {
            "query_string": {"query": term},
        },
        "aggregations": {
            "result_type": {
                "terms": {
                    "field": "result_type"
                }
            }
        }
    }

    if len(filters) > 0:
        query_filters = []
        for key, value in filters.items():
            query_filters.append({"term": {key: value}})

        query["filter"] = {
            "bool": {
                "must": query_filters
            }
        }

    index_name = SearchItem.Meta.es_index_name
    es_results = settings.ES_CLIENT.search(index=index_name, body=query)
    result = transform_search_result(es_result=es_results, term=term, filters=filters)
    return result


def parsefilters(filters):
    parsed_filters = {}
    for filter_item in filters:
        split = filter_item.split(":")
        parsed_filters[split[0]] = split[1]

    return parsed_filters


# /search?term=fred&filter=name:value&filter=name:value&page=1
def search(request):
    term = request.GET.get('term', '')
    filters = parsefilters(request.GET.getlist('filter'))
    result = es_search(term=term, filters=filters)
    return HttpResponse(json.dumps(result), content_type='application/json')
