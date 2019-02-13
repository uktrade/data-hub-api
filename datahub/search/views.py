"""Search views."""
from collections import namedtuple
from itertools import islice

from django.conf import settings
from django.utils.text import capfirst
from django.utils.timezone import now
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.core.csv import create_csv_response
from datahub.core.exceptions import DataHubException
from datahub.oauth.scopes import Scope
from datahub.search.apps import get_search_apps
from datahub.search.execute_query import execute_autocomplete_query, execute_search_query
from datahub.search.permissions import (
    has_permissions_for_app,
    SearchAndExportPermissions,
    SearchPermissions,
)
from datahub.search.query_builder import (
    get_basic_search_query,
    get_search_by_entity_query,
    limit_search_query,
)
from datahub.search.serializers import (
    AutocompleteSearchQuerySerializer,
    BasicSearchQuerySerializer,
    EntitySearchQuerySerializer,
)
from datahub.search.utils import SearchOrdering
from datahub.user_event_log.constants import USER_EVENT_TYPES
from datahub.user_event_log.utils import record_user_event

EntitySearch = namedtuple('EntitySearch', ['model', 'name'])


class SearchBasicAPIView(APIView):
    """Aggregate all entities search view."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)

    required_scopes = (Scope.internal_front_end,)
    http_method_names = ('get',)
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }

    def get(self, request, format=None):
        """Performs basic search."""
        serializer = BasicSearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated_params = serializer.validated_data
        ordering = _map_es_ordering(validated_params['sortby'], self.es_sort_by_remappings)

        query = get_basic_search_query(
            term=validated_params['term'],
            entities=(validated_params['entity'],),
            permission_filters_by_entity=dict(_get_permission_filters(request)),
            ordering=ordering,
            offset=validated_params['offset'],
            limit=validated_params['limit'],
        )

        results = execute_search_query(query)

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
    permission_classes = (IsAuthenticatedOrTokenHasScope, SearchPermissions)
    FILTER_FIELDS = []
    REMAP_FIELDS = {}

    # creates "or" query with a list of fields for given filter name
    # filter must exist in FILTER_FIELDS
    COMPOSITE_FILTERS = {}
    # Remappings from sortby values in the request to the actual field path in the search model
    # e.g. 'name' to 'name.keyword'
    es_sort_by_remappings = {}

    serializer_class = EntitySearchQuerySerializer
    entity = None
    fields_to_include = None
    fields_to_exclude = None

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
        return serializer.validated_data

    def get_base_query(self, request, validated_data):
        """Gets a filtered Elasticsearch query for the provided search parameters."""
        filter_data = self._get_filter_data(validated_data)
        permission_filters = self.search_app.get_permission_filters(request)
        ordering = _map_es_ordering(validated_data['sortby'], self.es_sort_by_remappings)

        return get_search_by_entity_query(
            entity=self.entity,
            term=validated_data['original_query'],
            filter_data=filter_data,
            composite_field_mapping=self.COMPOSITE_FILTERS,
            permission_filters=permission_filters,
            ordering=ordering,
            fields_to_include=self.fields_to_include,
            fields_to_exclude=self.fields_to_exclude,
        )

    def post(self, request, format=None):
        """Performs search."""
        data = request.data.copy()

        # to support legacy paging parameters that can be in query_string
        for legacy_query_param in ('limit', 'offset'):
            if legacy_query_param in request.query_params \
                    and legacy_query_param not in request.data:
                data[legacy_query_param] = request.query_params[legacy_query_param]

        validated_data = self.validate_data(data)
        query = self.get_base_query(request, validated_data)

        limited_query = limit_search_query(
            query,
            offset=validated_data['offset'],
            limit=validated_data['limit'],
        )

        results = execute_search_query(limited_query)

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits],
        }

        response = self.enhance_response(results, response)

        return Response(data=response)

    def enhance_response(self, results, response):
        """Placeholder for a method to enhance the response with custom data."""
        return response


class SearchExportAPIView(SearchAPIView):
    """Returns CSV file with all search results."""

    permission_classes = (IsAuthenticatedOrTokenHasScope, SearchAndExportPermissions)
    queryset = None
    field_titles = None
    db_sort_by_remappings = {}

    def post(self, request, format=None):
        """Performs search and returns CSV file."""
        validated_data = self.validate_data(request.data)

        es_query = self._get_es_query(request, validated_data)
        ids = tuple(self._get_ids(es_query))
        db_queryset = self._get_rows(ids, validated_data['sortby'])
        base_filename = self._get_base_filename()

        user_event_data = {
            'num_results': len(ids),
            'args': validated_data,
        }

        record_user_event(request, USER_EVENT_TYPES.search_export, data=user_event_data)

        return create_csv_response(db_queryset, self.field_titles, base_filename)

    def _get_base_filename(self):
        """Gets the filename (without the .csv suffix) for the CSV file download."""
        filename_parts = [
            'Data Hub',
            str(capfirst(self.queryset.model._meta.verbose_name_plural)),
            now().strftime('%Y-%m-%d-%H-%M-%S'),
        ]
        return ' - '.join(filename_parts)

    def _get_ids(self, es_query):
        """
        Gets the document IDs from an Elasticsearch query using the scroll API.

        The number of IDs returned is limited by settings.SEARCH_EXPORT_MAX_RESULTS.
        """
        for hit in islice(es_query.scan(), settings.SEARCH_EXPORT_MAX_RESULTS):
            yield hit.meta.id

    def _get_es_query(self, request, validated_data):
        """Gets a scannable Elasticsearch query for the current request."""
        return self.get_base_query(
            request,
            validated_data,
        ).source(
            # Stops _source from being returned in the responses
            fields=False,
        ).params(
            # Keeps the sort order that the user specified
            preserve_order=True,
            # Number of results in each scroll response
            size=settings.SEARCH_EXPORT_SCROLL_CHUNK_SIZE,
        )

    def _get_rows(self, ids, search_ordering):
        """
        Returns an iterable using QuerySet.iterator() over the search results.

        The search sort-by value is translated to a value compatible with the Django ORM and
        applied to the query set to preserve the original sort order.

        At the moment, all rows are fetched in one query (using a server-side cursor) as
        settings.SEARCH_EXPORT_MAX_RESULTS is set to a (relatively) low value.
        """
        db_ordering = self._translate_search_ordering_to_django_ordering(search_ordering)

        return self.queryset.filter(
            pk__in=ids,
        ).order_by(
            *db_ordering,
        ).values(
            *self.field_titles.keys(),
        ).iterator()

    def _translate_search_ordering_to_django_ordering(self, ordering):
        """
        Converts a sort-by value as used in the search API to a tuple of values that can be
        passed to QuerySet.order_by().

        Note that this relies on the same field names having been used; if they differ then you
        should manually specify a remapping in the db_sort_by_remappings class attribute.
        """
        if not ordering:
            return ()

        auto_translated_field = ordering.field.replace('.', '__')
        db_field = self.db_sort_by_remappings.get(ordering.field, auto_translated_field)
        prefix = '-' if ordering.is_descending else ''

        return f'{prefix}{db_field}', 'pk'


class AutocompleteSearchListAPIView(ListAPIView):
    """Autocomplete search base list view for type ahead."""

    search_app = None
    permission_classes = (IsAuthenticatedOrTokenHasScope, SearchPermissions)
    document_fields = None

    def list(self, request, *args, **kwargs):
        """Executes the elasticsearch query"""
        serializer = AutocompleteSearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated_params = serializer.validated_data

        self.check_permission_filters()
        results = execute_autocomplete_query(
            self.search_app.es_model,
            validated_params['term'],
            validated_params['limit'],
            fields_to_include=self.document_fields,
        )

        return Response(data={
            'count': len(results),
            'results': [result['_source'].to_dict() for result in results],
        })

    def check_permission_filters(self):
        """
        Checks for permission filters associated with the search app
        and if present rasies an error.
        """
        permission_filters = self._get_permission_filters()
        if permission_filters is not None:
            raise DataHubException(
                'Unable to apply filtering for autocomplete search request',
            )

    def _get_permission_filters(self):
        return self.search_app.get_permission_filters(self.request)


def _map_es_ordering(ordering, mapping):
    if not ordering:
        return None

    remapped_field = mapping.get(ordering.field, ordering.field)
    return SearchOrdering(remapped_field, ordering.direction)
