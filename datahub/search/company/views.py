from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company
from .. import elasticsearch


class SearchCompanyAPIView(APIView):
    """Filtered company search view."""

    SORT_BY_FIELDS = (
        'account_manager.name',
        'alias',
        'archived',
        'archived_by',
        'business_type.name',
        'classification.name',
        'companies_house_data.company_number',
        'company_number',
        'contacts.name',
        'created_on',
        'employee_range.name',
        'export_to_countries.name',
        'future_interest_countries.name',
        'headquarter_type.name',
        'id',
        'modified_on',
        'name',
        'registered_address_town',
        'sector.name',
        'trading_address_town',
        'turnover_range.name',
        'uk_based',
        'uk_region.name'
    )

    FILTER_FIELDS = (
        'account_manager',
        'alias',
        'description',
        'export_to_country',
        'future_interest_country',
        'name',
        'sector',
        'trading_address_country',
        'trading_address_postcode',
        'trading_address_town',
        'uk_based',
        'uk_region'
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered company search."""
        filters = {elasticsearch.remap_filter_id_field(field): request.data[field]
                   for field in self.FILTER_FIELDS if field in request.data}

        original_query = request.data.get('original_query', '')

        sortby = request.data.get('sortby')
        if sortby:
            field = sortby.rsplit(':')[0]
            if field not in self.SORT_BY_FIELDS:
                raise ValidationError(f'"sortby" field is not one of {self.SORT_BY_FIELDS}.')

        offset = int(request.data.get('offset', 0))
        limit = int(request.data.get('limit', 100))

        results = elasticsearch.get_search_by_entity_query(
            entity=Company,
            term=original_query,
            filters=filters,
            field_order=sortby,
            offset=offset,
            limit=limit,
        ).execute()

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits],
        }

        return Response(data=response)
