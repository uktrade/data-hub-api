from rest_framework.exceptions import ValidationError
from rest_framework.pagination import _positive_int
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from .models import Order
from .. import elasticsearch


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


class SearchOrderAPIView(PaginatedAPIMixin, APIView):
    """Filtered order search view."""

    http_method_names = ('post',)
    DEFAULT_ORDERING = 'created_on:desc'

    FILTER_FIELDS = [
        'primary_market',
        'created_on_before',
        'created_on_after',
        'assigned_to_adviser',
        'assigned_to_team',
    ]

    REMAP_FIELDS = {
        'primary_market': 'primary_market.id',
        'assigned_to_adviser': 'assignees.id',
        'assigned_to_team': 'assignees.dit_team.id',
    }

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
        """Perform filtered order search."""
        limit, offset = self.get_pagination_values(request)
        filters, ranges = self.get_filtering_data(request)

        results = elasticsearch.get_search_by_entity_query(
            entity=Order,
            term='',
            filters=filters,
            ranges=ranges,
            field_order=self.DEFAULT_ORDERING,
            offset=offset,
            limit=limit,
        ).execute()

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits]
        }

        return Response(data=response)
