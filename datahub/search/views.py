"""Search views."""
import uuid
from collections import namedtuple

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import _positive_int
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from . import elasticsearch
from .apps import get_search_apps

EntitySearch = namedtuple('EntitySearch', ['model', 'name', 'plural_name'])


class PaginatedAPIMixin:
    """Mixin for paginated API Views."""

    default_limit = api_settings.PAGE_SIZE
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_results = 10000

    def get_limit(self, request):
        """Return the limit specified by the user or the default one."""
        if self.limit_query_param:
            try:
                return _positive_int(
                    request.data[self.limit_query_param],
                    strict=True
                )
            except (KeyError, ValueError):
                pass

        return self.default_limit

    def get_offset(self, request):
        """Return the offset specified by the user or the default one."""
        try:
            return _positive_int(
                request.data[self.offset_query_param],
            )
        except (KeyError, ValueError):
            return 0

    def get_pagination_values(self, request):
        """Return the pagination values (limit, offset) or raises ValidationError."""
        limit = self.get_limit(request)
        offset = self.get_offset(request)

        if limit + offset > self.max_results:
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: (
                    'Invalid offset/limit. '
                    f'Result window cannot be greater than {self.max_results}'
                )
            })
        return limit, offset


class SearchWithFiltersAPIMixin(PaginatedAPIMixin):
    """Mixin for Search with filters views."""

    DEFAULT_ORDERING = None
    SORT_BY_FIELDS = {}
    FILTER_FIELDS = {}
    REMAP_FIELDS = {}

    # Specify entity you want to search in (eg. Company, Contact, InvestmentProject and so on...)
    entity = None
    with_aggregations = False

    http_method_names = ('post',)

    def validate_filter_value(self, field, value):
        """Checks if supplied value for given field is valid."""
        es_field = self.REMAP_FIELDS.get(field, field)
        if isinstance(value, list):
            if not all(isinstance(item, (int, str,)) for item in value):
                raise ValueError({field: 'Contains invalid values in the list.'})
        elif es_field.endswith('.id'):
            try:
                uuid.UUID(value)
            except ValueError:
                raise ValueError({field: 'Contains invalid id.'})
        elif isinstance(value, dict):
            raise ValueError({field: 'Contains invalid value.'})

        return value

    def get_filtering_data(self, request):
        """Return (filters, date ranges) to be used to query ES."""
        try:
            filters = {
                self.REMAP_FIELDS.get(field, field):
                    self.validate_filter_value(field, request.data[field])
                for field in self.FILTER_FIELDS
                if field in request.data
            }
        except ValueError as e:
            raise ValidationError(e)

        try:
            filters, ranges = elasticsearch.date_range_fields(filters)
        except ValueError:
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: 'Date(s) in incorrect format.'
            })

        return filters, ranges

    def extract_aggregates(self, results):
        """Extracts aggregates from results."""
        aggregations = {}
        for field in self.FILTER_FIELDS:
            es_field = self.REMAP_FIELDS.get(field, field)
            if es_field in results.aggregations:
                aggregation = results.aggregations[es_field]
                if '.' in es_field:
                    aggregation = aggregation[es_field]

                aggregations[field] = [bucket.to_dict() for bucket in aggregation['buckets']]
        return aggregations

    def post(self, request, format=None):
        """Performs filtered contact search."""
        limit, offset = self.get_pagination_values(request)
        filters, ranges = self.get_filtering_data(request)

        original_query = request.data.get('original_query', '')

        sortby = request.data.get('sortby', self.DEFAULT_ORDERING)
        if sortby:
            field = sortby.rsplit(':')[0]
            if field not in self.SORT_BY_FIELDS:
                raise ValidationError(f'"sortby" field is not one of {self.SORT_BY_FIELDS}.')

        options = {
            'entity': self.entity,
            'term': original_query,
            'filters': filters,
            'ranges': ranges,
            'field_order': sortby,
            'offset': offset,
            'limit': limit,
        }
        if self.with_aggregations:
            options['aggs'] = [self.REMAP_FIELDS.get(field, field) for field in self.FILTER_FIELDS]

        results = elasticsearch.get_search_by_entity_query(
            **options
        ).execute()

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits],
        }

        if self.with_aggregations:
            response['aggregations'] = self.extract_aggregates(results)

        return Response(data=response)


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
            'aggregations': [{'count': x['doc_count'], 'entity': x['key']}
                             for x in results.aggregations['count_by_type']['buckets']],
        }

        hits = [x.to_dict() for x in results.hits]

        response[self.entity_by_name[entity].plural_name] = hits
        return Response(data=response)
