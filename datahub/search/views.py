"""Search views."""
from collections import namedtuple

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import elasticsearch
from .apps import get_search_apps


EntitySearch = namedtuple('EntitySearch', ['model', 'name', 'plural_name'])


class SearchBasicAPIView(APIView):
    """Aggregate all entities search view."""

    http_method_names = ('get',)

    SORT_BY_FIELDS = (
        'created_on',
        'name',
    )

    DEFAULT_ENTITY = 'company'

    def __init__(self, *args, **kwargs):
        """Initialises self.entity_by_name dynamically."""
        super().__init__(*args, **kwargs)

        self.entity_by_name = {
            search_app.name: EntitySearch(
                search_app.ESModel,
                search_app.name,
                search_app.plural_name
            )
            for search_app in get_search_apps()
        }

    def get(self, request, format=None):
        """Performs basic search."""
        if 'term' not in request.query_params:
            raise ValidationError('Missing required "term" field.')
        term = request.query_params['term']

        entity = request.query_params.get('entity', self.DEFAULT_ENTITY)
        if entity not in (self.entity_by_name):
            raise ValidationError(
                f'Entity is not one of {", ".join(self.entity_by_name)}'
            )

        sortby = request.query_params.get('sortby')
        if sortby:
            field = sortby.rsplit(':')[0]
            if field not in self.SORT_BY_FIELDS:
                raise ValidationError(f'"sortby" field is not one of {self.SORT_BY_FIELDS}.')

        offset = int(request.query_params.get('offset', 0))
        limit = int(request.query_params.get('limit', 100))

        results = elasticsearch.get_basic_search_query(
            term=term,
            entities=(self.entity_by_name[entity].model,),
            field_order=sortby,
            offset=offset,
            limit=limit
        ).execute()

        response = {
            'count': results.hits.total,
            'results': [result.to_dict() for result in results.hits],
            'aggregations': [{'count': x['doc_count'], 'entity': x['key']}
                             for x in results.aggregations['count_by_type']['buckets']],
        }

        return Response(data=response)
