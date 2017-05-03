"""Search views."""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import elasticsearch


class SearchBasicAPIView(APIView):
    """Aggregate company and contact search view."""

    http_method_names = ('get',)

    def get(self, request, format=None):
        """Performs basic search."""
        term = request.query_params['term']
        entity = request.query_params.get('entity', 'company')
        offset = int(request.query_params.get('offset', 0))
        limit = int(request.query_params.get('limit', 100))

        results = elasticsearch.get_basic_search_query(
            term=term,
            entities=entity.split(','),
            offset=offset,
            limit=limit
        ).execute()

        response = {
            'count': results.hits.total,
            'aggregations': list(map(lambda x: {'count': x['doc_count'], 'entity': x['key']},
                                     results.aggregations['count_by_type']['buckets'])),
        }

        hits = list(map(lambda x: x.to_dict(), results.hits))

        if entity == 'company':
            response.update({'companies': hits})
        elif entity == 'contact':
            response.update({'contacts': hits})

        return Response(data=response)


class SearchCompanyAPIView(APIView):
    """Filtered company search view."""

    COMPANY_FILTER_FIELDS = (
        'name', 'alias', 'sector', 'account_manager', 'export_to_country',
        'future_interest_country', 'description', 'uk_region',
        'trading_address_town', 'trading_address_country', 'trading_address_postcode',
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered company search."""
        filters = {field: request.data[field]
                   for field in self.COMPANY_FILTER_FIELDS if field in request.data}
        filters = elasticsearch.remap_fields(filters)

        if len(filters.keys()) == 0:
            raise ValidationError('Missing required at least one filter.')

        original_query = request.data.get('original_query')

        offset = int(request.query_params.get('offset', 0))
        limit = int(request.query_params.get('limit', 100))

        results = elasticsearch.get_search_company_query(
            term=original_query,
            filters=filters,
            offset=offset,
            limit=limit,
        ).execute()

        response = {
            'count': results.hits.total,
            'results': list(map(lambda x: x.to_dict(), results.hits)),
        }

        return Response(data=response)


class SearchContactAPIView(APIView):
    """Filtered contact search view."""

    CONTACT_FILTER_FIELDS = (
        'first_name', 'last_name', 'job_title', 'company', 'advisor', 'notes',
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered contact search."""
        filters = {field: request.data[field]
                   for field in self.CONTACT_FILTER_FIELDS if field in request.data}

        filters = elasticsearch.remap_fields(filters)

        if len(filters.keys()) == 0:
            raise ValidationError('Missing required at least one filter.')

        original_query = request.data.get('original_query')

        offset = int(request.data.get('offset', 0))
        limit = int(request.data.get('limit', 100))

        results = elasticsearch.get_search_contact_query(
            term=original_query,
            filters=filters,
            offset=offset,
            limit=limit,
        ).execute()

        response = {
            'count': results.hits.total,
            'results': list(map(lambda x: x.to_dict(), results.hits)),
        }

        return Response(data=response)
