"""Search views."""
from collections import namedtuple
from enum import auto, Enum
from itertools import islice

from django.conf import settings
from django.utils.text import capfirst
from django.utils.timezone import now
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView

from datahub.core.csv import create_csv_response
from datahub.core.exceptions import DataHubException
from datahub.oauth.scopes import Scope
from datahub.search.apps import get_global_search_apps_as_mapping
from datahub.search.execute_query import execute_autocomplete_query, execute_search_query
from datahub.search.permissions import (
    has_permissions_for_app,
    SearchAndExportPermissions,
    SearchPermissions,
)
from datahub.search.query_builder import (
    get_basic_search_query,
    get_search_by_entities_query,
    limit_search_query,
)
from datahub.search.serializers import (
    AutocompleteSearchQuerySerializer,
    BasicSearchQuerySerializer,
    EntitySearchQuerySerializer,
)
from datahub.search.utils import SearchOrdering
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.utils import record_user_event


class SearchStubSchema(AutoSchema):
    """
    AutoSchema with supressed responses schema.

    The search response has different schema than the request. This prevents showing
    wrong example in the OpenAPI docs.
    """

    def get_operation(self, path, method):
        """
        Supress showing the response in the form of the request body.
        """
        operation = super().get_operation(path, method)

        operation['responses'] = {
            '200': {
                'description': '',
                'content': {
                    'application/json': {
                        'schema': {},
                    },
                },
            },
        }

        return operation


class SearchBasicStubSchema(SearchStubSchema):
    """
    SearchStubSchema with defined query parameters to allow query basic search from the Open API
    docs.
    """

    def get_operation(self, path, method):
        """Include parameters to query the basic search endpoint."""
        operation = super().get_operation(path, method)
        operation['parameters'] = [
            {
                'description': '',
                'in': 'query',
                'name': 'term',
                'required': True,
                'schema': {
                    'type': 'string',
                },
            },
            {
                'description': '',
                'in': 'query',
                'name': 'entity',
                'required': False,
                'schema': {
                    'type': 'string',
                },
            },
        ]
        return operation


EntitySearch = namedtuple('EntitySearch', ['model', 'name'])

v3_view_registry = {}
v4_view_registry = {}

SHARED_FIELDS_TO_EXCLUDE = ('_document_type',)


class SearchBasicAPIView(APIView):
    """Aggregate all entities search view."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)

    required_scopes = (Scope.internal_front_end,)
    http_method_names = ('get',)
    schema = SearchBasicStubSchema()

    fields_to_exclude = (
        'export_countries',
        'were_countries_discussed',
    )

    def get(self, request, format=None):
        """Performs basic search."""
        serializer = BasicSearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated_params = serializer.validated_data

        fields_to_exclude = (
            *SHARED_FIELDS_TO_EXCLUDE,
            *(self.fields_to_exclude or ()),
        )

        query = get_basic_search_query(
            entity=validated_params['entity'],
            term=validated_params['term'],
            permission_filters_by_entity=dict(_get_global_search_permission_filters(request)),
            offset=validated_params['offset'],
            limit=validated_params['limit'],
            fields_to_exclude=fields_to_exclude,
        )

        results = execute_search_query(query)

        response = {
            'count': results.hits.total,
            'results': [result.to_dict() for result in results.hits],
            'aggregations': [{'count': x['doc_count'], 'entity': x['key']}
                             for x in results.aggregations['count_by_type']['buckets']],
        }

        return Response(data=response)


def _get_global_search_permission_filters(request):
    """
    Gets the permissions filters that should be applied to each search entity (to enforce
    permissions) in global search.

    Only global search entities that the user has access to are returned.
    """
    for app in get_global_search_apps_as_mapping().values():
        if not has_permissions_for_app(request, app):
            continue

        filter_args = app.get_permission_filters(request)
        yield (app.es_model.get_app_name(), filter_args)


class SearchAPIView(APIView):
    """Filtered search view."""

    schema = SearchStubSchema()

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

    def get_entities(self):
        """Returns entities"""
        return [self.search_app.es_model]

    def validate_data(self, data):
        """Validate and clean data."""
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def get_base_query(self, request, validated_data):
        """Gets a filtered Elasticsearch query for the provided search parameters."""
        filter_data = self._get_filter_data(validated_data)
        entities = self.get_entities()
        permission_filters = self.search_app.get_permission_filters(request)
        ordering = _map_es_ordering(validated_data['sortby'], self.es_sort_by_remappings)

        fields_to_exclude = (
            *SHARED_FIELDS_TO_EXCLUDE,
            *(self.fields_to_exclude or ()),
        )

        return get_search_by_entities_query(
            entities=entities,
            term=validated_data['original_query'],
            filter_data=filter_data,
            composite_field_mapping=self.COMPOSITE_FILTERS,
            permission_filters=permission_filters,
            ordering=ordering,
            fields_to_include=self.fields_to_include,
            fields_to_exclude=fields_to_exclude,
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

    def get_serializer(self):
        """Return query serializer for use with OpenAPI documentation."""
        return self.serializer_class()


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

        record_user_event(request, UserEventType.SEARCH_EXPORT, data=user_event_data)

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
    autocomplete_context_serializer_class = None

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
            self.document_fields,
            self.get_search_context(request.query_params),
        )
        return Response(data={
            'count': len(results),
            'results': [result['_source'].to_dict() for result in results],
        })

    def get_search_context(self, query_params):
        """
        Add context (filters) to the autocomplete search if provided.
        """
        if not self.autocomplete_context_serializer_class:
            return {}
        serializer = self.autocomplete_context_serializer_class(data=query_params)
        serializer.is_valid()
        return serializer.validated_data

    def check_permission_filters(self):
        """
        Checks for permission filters associated with the search app
        and if present raises an error.
        """
        permission_filters = self._get_permission_filters()
        if permission_filters is not None:
            raise DataHubException(
                'Unable to apply filtering for autocomplete search request',
            )

    def _get_permission_filters(self):
        return self.search_app.get_permission_filters(self.request)


class ViewType(Enum):
    """Types of views."""

    # The standard type (no special prefix)
    default = auto()
    # Use a public prefix (e.g. /v4/public/search/company)
    public = auto()


def register_v3_view(sub_path=None):
    """
    Decorator that registers a v3 search view.

    :param sub_path: optional sub-path to add to the URL

    TODO: This should be removed when the migration to v4 is complete.

    Examples:
       For the main entity search view at `/v3/search/<app name>`:

       @register_v4_view()
       class SearchView(...):
          ...

       For a CSV export view at `/v3/search/<app name>/export`:

       @register_v4_view(name='export')
       class SearchView(...):
          ...

    """
    def inner(view_cls):
        _register_view(v3_view_registry, view_cls.search_app, view_cls, 'v3', sub_path=sub_path)
        return view_cls

    return inner


def register_v4_view(sub_path=None, is_public=False):
    """
    Decorator that registers a v4 search view.

    :param sub_path: optional sub-path to add to the URL
    :param is_public: if True, the URL path will have a /v4/public prefix instead of just /v4

    Examples:
       For the main entity search view at `/v4/search/<app sub_path>`:

           @register_v4_view()
           class SearchView(...):
              ...

       For a CSV export view at `/v4/search/<app sub_path>/export`:

           @register_v4_view(sub_path='export')
           class SearchView(...):
              ...

       For a view at `/v4/public/search/<app sub_path>`:

           @register_v4_view(is_public=True)
           class SearchView(...):
              ...

    """
    def inner(view_cls):
        _register_view(
            v4_view_registry,
            view_cls.search_app,
            view_cls,
            'v4',
            sub_path=sub_path,
            is_public=is_public,
        )
        return view_cls

    return inner


def _register_view(
    view_mapping,
    search_app,
    view_cls,
    version_for_error,
    sub_path=None,
    is_public=False,
):
    view_type = ViewType.public if is_public else ViewType.default

    if (search_app, view_type, sub_path) in view_mapping:
        raise ValueError(
            f'There is already a {version_for_error} view with sub_path {sub_path} for search app '
            f'{search_app.__name__}',
        )

    view_mapping[(search_app, view_type, sub_path)] = view_cls


def _map_es_ordering(ordering, mapping):
    if not ordering:
        return None

    remapped_field = mapping.get(ordering.field, ordering.field)
    return SearchOrdering(remapped_field, ordering.direction)
