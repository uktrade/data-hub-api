from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.response import Response

from datahub.oauth.scopes import Scope
from datahub.search.execute_query import execute_search_query
from datahub.search.exportcountryhistory import ExportCountryHistoryApp
from datahub.search.permissions import SearchPermissions
from datahub.search.query_builder import get_search_by_entity_query, limit_search_query
from datahub.search.serializers import EntitySearchQuerySerializer
from datahub.search.views import _map_es_ordering, register_v4_view, SearchAPIView


@register_v4_view()
class ExportCountryHistoryView(SearchAPIView):
    """Export country history search view."""

    required_scopes = (Scope.internal_front_end,)
    search_app = ExportCountryHistoryApp

    permission_classes = (IsAuthenticatedOrTokenHasScope, SearchPermissions)
    FILTER_FIELDS = [
        'history_user',
        'country',
        'company',
    ]

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
            self.search_app.es_model,
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
