import json
from django.http import HttpResponse
from api.services.searchservice import search as es_search


def parse_filters(filters):
    parsed_filters = {}
    for filter_item in filters:
        split = filter_item.split(":")
        parsed_filters[split[0]] = split[1]

    return parsed_filters


# /search?term=fred&filter=name:value&filter=name:value&page=1
def search(request):
    params = {
        "term": request.GET.get('term', ''),
        "filters": parse_filters(request.GET.getlist('filter')),
        "page": int(request.GET.get('page', '1')),
    }

    result = es_search(**params)
    result.update(**params)

    return HttpResponse(json.dumps(result), content_type='application/json')
