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
        if 'term' not in request.query_params:
            raise ValidationError('Missing required "term" field.')
        term = request.query_params['term']

        entity = request.query_params.get('entity', 'company')
        if entity not in ('company', 'contact', 'investment_project'):
            raise ValidationError('Entity is not one of "company", "contact" or "investment_project".')

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
            'aggregations': [{'count': x['doc_count'], 'entity': x['key']}
                             for x in results.aggregations['count_by_type']['buckets']],
        }

        hits = [x.to_dict() for x in results.hits]

        if entity == 'company':
            response['companies'] = hits
        elif entity == 'contact':
            response['contacts'] = hits
        elif entity == 'investment_project':
            response['investment_projects'] = hits

        return Response(data=response)


class SearchCompanyAPIView(APIView):
    """Filtered company search view."""

    FILTER_FIELDS = (
        'name', 'alias', 'sector', 'account_manager', 'export_to_country',
        'future_interest_country', 'description', 'uk_region', 'uk_based',
        'trading_address_town', 'trading_address_country', 'trading_address_postcode',
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered company search."""
        filters = {field: request.data[field]
                   for field in self.FILTER_FIELDS if field in request.data}
        filters = elasticsearch.remap_fields(filters)

        if len(filters.keys()) == 0:
            raise ValidationError('Missing required at least one filter.')

        original_query = request.data.get('original_query', '')

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
            'results': [x.to_dict() for x in results.hits],
        }

        return Response(data=response)


class SearchContactAPIView(APIView):
    """Filtered contact search view."""

    FILTER_FIELDS = (
        'first_name', 'last_name', 'job_title', 'company', 'adviser', 'notes',
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered contact search."""
        filters = {field: request.data[field]
                   for field in self.FILTER_FIELDS if field in request.data}

        filters = elasticsearch.remap_fields(filters)

        if len(filters.keys()) == 0:
            raise ValidationError('Missing required at least one filter.')

        original_query = request.data.get('original_query', '')

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
            'results': [x.to_dict() for x in results.hits],
        }

        return Response(data=response)


class SearchInvestmentProjectAPIView(APIView):
    """Filtered investment project search view."""

    FILTER_FIELDS = (
        'client_relationship_manager', 'description', 'estimated_land_date_after',
        'estimated_land_date_before', 'investor_company', 'investment_type',
        'phase', 'sector'
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered contact search."""
        filters = {field: request.data[field]
                   for field in self.FILTER_FIELDS if field in request.data}

        filters = elasticsearch.remap_fields(filters)
        if len(filters.keys()) == 0:
            raise ValidationError('Missing required at least one filter.')

        try:
            filters, ranges = elasticsearch.date_range_fields(filters)
        except ValueError:
            raise ValidationError('Date(s) in incorrect format.')

        offset = int(request.data.get('offset', 0))
        limit = int(request.data.get('limit', 100))

        results = elasticsearch.get_search_investment_project_query(
            term='',
            filters=filters,
            ranges=ranges,
            offset=offset,
            limit=limit,
        ).execute()

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits],
        }

        return Response(data=response)
