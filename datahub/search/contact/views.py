from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Contact
from .. import elasticsearch


class SearchContactAPIView(APIView):
    """Filtered contact search view."""

    SORT_BY_FIELDS = (
        'address_country.name',
        'address_county',
        'address_same_as_company',
        'address_town',
        'adviser.name',
        'archived',
        'archived_by.name',
        'company.name',
        'contactable_by_dit',
        'contactable_by_dit_partners',
        'contactable_by_email',
        'contactable_by_phone',
        'created_on',
        'email',
        'first_name',
        'id',
        'job_title',
        'last_name',
        'modified_on',
        'name',
        'primary',
        'telephone_countrycode',
        'telephone_number',
        'title.name'
    )

    FILTER_FIELDS = (
        'company_name',
        'company_sector',
        'company_uk_region',
        'address_country',
    )

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered contact search."""
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
            entity=Contact,
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
