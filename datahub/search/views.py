"""Search views."""
from collections import namedtuple

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from . import elasticsearch
from .apps import get_search_apps
from .serializers import SearchSerializer

EntitySearch = namedtuple('EntitySearch', ['model', 'name'])


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


class SearchAPIView(APIView):
    """Filtered investment project search view."""

    FILTER_FIELDS = []
    REMAP_FIELDS = {}

    serializer_class = SearchSerializer
    entity = None

    include_aggregations = False

    http_method_names = ('post',)

    def get_filtering_data(self, request):
        """Return (filters, date ranges) to be used to query ES."""
        filters = {
            self.REMAP_FIELDS.get(field, field): request.data[field]
            for field in self.FILTER_FIELDS
            if field in request.data
        }

        try:
            filters, ranges = elasticsearch.date_range_fields(filters)
        except ValueError:
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: 'Date(s) in incorrect format.'
            })

        return filters, ranges

    def post(self, request, format=None):
        """Performs search."""
        data = request.data.copy()

        # to support legacy paging parameters that can be in query_string
        for legacy_query_param in ('limit', 'offset',):
            if legacy_query_param in request.query_params \
                    and legacy_query_param not in request.data:
                data[legacy_query_param] = request.query_params[legacy_query_param]

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        filters, ranges = self.get_filtering_data(request)

        results = elasticsearch.get_search_by_entity_query(
            entity=self.entity,
            term=validated_data['original_query'],
            filters=filters,
            ranges=ranges,
            field_order=validated_data['sortby'],
            include_aggregations=self.include_aggregations,
            offset=validated_data['offset'],
            limit=validated_data['limit'],
        ).execute()

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits],
        }

        if self.include_aggregations:
            aggregations = {}
            for field in self.FILTER_FIELDS:
                es_field = elasticsearch.remap_filter_id_field(field)
                if es_field in results.aggregations:
                    aggregation = results.aggregations[es_field]
                    if '.' in es_field:
                        aggregation = aggregation[es_field]

                    aggregations[field] = [bucket.to_dict() for bucket in aggregation['buckets']]

            response['aggregations'] = aggregations

        return Response(data=response)
