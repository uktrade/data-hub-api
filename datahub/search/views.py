"""Search views."""
import csv
from collections import namedtuple
from datetime import datetime

from django.http import StreamingHttpResponse
from django.utils.text import slugify
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.oauth.scopes import Scope
from . import elasticsearch
from .apps import get_search_apps
from .permissions import has_permissions_for_app, SearchAppPermissions
from .serializers import SearchSerializer
from .utils import Echo

EntitySearch = namedtuple('EntitySearch', ['model', 'name'])


class SearchBasicAPIView(APIView):
    """Aggregate all entities search view."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)

    required_scopes = (Scope.internal_front_end,)
    http_method_names = ('get',)

    SORT_BY_FIELDS = (
        'created_on',
        'name',
    )

    DEFAULT_ENTITY = 'company'

    IGNORED_ENTITIES = (
        'companieshousecompany',
    )

    def __init__(self, *args, **kwargs):
        """Initialises self.entity_by_name dynamically."""
        super().__init__(*args, **kwargs)

        self.entity_by_name = {
            search_app.name: EntitySearch(
                search_app.es_model,
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
            permission_filters_by_entity=dict(_get_permission_filters(request)),
            field_order=sortby,
            ignored_entities=self.IGNORED_ENTITIES,
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


def _get_permission_filters(request):
    """
    Gets the permissions filters that should be applied to each search entity (to enforce
    permissions).

    Only entities that the user has access are returned.
    """
    for app in get_search_apps():
        if not has_permissions_for_app(request, app):
            continue

        filter_args = app.get_permission_filters(request)
        yield (app.es_model._doc_type.name, filter_args)


class SearchAPIView(APIView):
    """Filtered search view."""

    search_app = None
    permission_classes = (IsAuthenticatedOrTokenHasScope, SearchAppPermissions)
    FILTER_FIELDS = []
    REMAP_FIELDS = {}

    # creates "or" query with a list of fields for given filter name
    # filter must exist in FILTER_FIELDS
    COMPOSITE_FILTERS = {}

    serializer_class = SearchSerializer
    entity = None

    include_aggregations = False

    http_method_names = ('post',)

    def _get_filter_data(self, validated_data):
        """Returns filter data."""
        filters = {
            self.REMAP_FIELDS.get(field, field): validated_data[field]
            for field in self.FILTER_FIELDS
            if field in validated_data
        }
        return filters

    def validate_data(self, data):
        """Validate and clean data."""
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # prepare default values
        cleaned_data = {
            k: v.default for k, v in serializer.fields.items()
            if v.default is not empty
        }
        if serializer.DEFAULT_ORDERING:
            cleaned_data['sortby'] = serializer.DEFAULT_ORDERING

        # update with validated data
        cleaned_data.update({
            k: v for k, v in validated_data.items()
            if k in data
        })
        return cleaned_data

    def post(self, request, format=None):
        """Performs search."""
        data = request.data.copy()

        # to support legacy paging parameters that can be in query_string
        for legacy_query_param in ('limit', 'offset',):
            if legacy_query_param in request.query_params \
                    and legacy_query_param not in request.data:
                data[legacy_query_param] = request.query_params[legacy_query_param]

        validated_data = self.validate_data(data)
        filter_data = self._get_filter_data(validated_data)
        permission_filters = self.search_app.get_permission_filters(request)

        aggregations = (self.REMAP_FIELDS.get(field, field) for field in self.FILTER_FIELDS) \
            if self.include_aggregations else None

        query = elasticsearch.get_search_by_entity_query(
            entity=self.entity,
            term=validated_data['original_query'],
            filter_data=filter_data,
            composite_filters=self.COMPOSITE_FILTERS,
            permission_filters=permission_filters,
            field_order=validated_data['sortby'],
            aggregations=aggregations,
        )

        results = elasticsearch.limit_search_query(
            query,
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
                es_field = self.REMAP_FIELDS.get(field, field)
                if es_field in results.aggregations:
                    aggregation = results.aggregations[es_field]
                    if '.' in es_field:
                        aggregation = aggregation[es_field]

                    aggregations[field] = [bucket.to_dict() for bucket in aggregation['buckets']]

            response['aggregations'] = aggregations

        return Response(data=response)


class SearchExportAPIView(SearchAPIView):
    """Returns CSV file with all search results."""

    IGNORED_SUFFIXES = ('_trigram', '_keyword')

    def _clean_fieldnames(self, fieldnames):
        """Remove special fields from the export."""
        return [field for field in fieldnames
                if not any(field.endswith(suffix) for suffix in self.IGNORED_SUFFIXES)]

    def _format_cell(self, cell):
        """Gets cell or name from cell and flattens the cell if necessary."""
        if isinstance(cell, dict):
            for k in ('name', 'type', 'company_number', 'uri', 'id',):
                if k in cell:
                    return cell[k]
            return str(cell)

        if isinstance(cell, list):
            return ','.join(self._format_cell(item) for item in cell)

        return cell

    def _get_csv(self, writer, query):
        """Generates header and formatted search results."""
        # we want to keep the same order of rows that is in the search results
        query.params(preserve_order=True)
        # work around bug: https://bugs.python.org/issue27497
        header = dict(zip(writer.fieldnames, writer.fieldnames))
        yield writer.writerow(header)
        for hit in query.scan():
            yield writer.writerow({k: self._format_cell(v)
                                   for k, v in hit.to_dict().items() if k in writer.fieldnames})

    def _get_base_filename(self, original_query):
        """Gets base filename that contains sanitized entity name and original_query."""
        filename_parts = [
            datetime.utcnow().strftime('%Y-%m-%d'),
            'data-hub',
            self.entity.__name__
        ]
        if original_query:
            filename_parts.append(original_query)

        return slugify('-'.join(filename_parts))

    def _get_fieldnames(self):
        """Gets cleaned list of entity field names."""
        return self._clean_fieldnames(
            self.entity._doc_type.mapping.properties._params['properties'].keys()
        )

    def post(self, request, format=None):
        """Performs search and returns CSV file."""
        validated_data = self.validate_data(request.data)
        filter_data = self._get_filter_data(validated_data)

        results = elasticsearch.get_search_by_entity_query(
            entity=self.entity,
            term=validated_data['original_query'],
            filter_data=filter_data,
            field_order=validated_data['sortby'],
        )

        base_filename = self._get_base_filename(validated_data['original_query'])

        writer = csv.DictWriter(Echo(), fieldnames=sorted(self._get_fieldnames()))

        response = StreamingHttpResponse(self._get_csv(writer, results), content_type='text/csv')

        response['Content-Disposition'] = f'attachment; filename="{base_filename}.csv"'
        return response
