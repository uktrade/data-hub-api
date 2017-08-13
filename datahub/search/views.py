"""Search views."""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import elasticsearch
from .company.models import Company
from .contact.models import Contact
from .investment.models import InvestmentProject


class SearchBasicAPIView(APIView):
    """Aggregate company and contact search view."""

    http_method_names = ('get',)

    SORT_BY_FIELDS = (
        'created_on',
        'name',
    )

    ENTITY_BY_NAME = {
        'company': Company,
        'contact': Contact,
        'investment_project': InvestmentProject,
    }

    def get(self, request, format=None):
        """Performs basic search."""
        if 'term' not in request.query_params:
            raise ValidationError('Missing required "term" field.')
        term = request.query_params['term']

        entity = request.query_params.get('entity', 'company')
        if entity not in ('company', 'contact', 'investment_project'):
            raise ValidationError('Entity is not one of "company", "contact" or '
                                  '"investment_project".')

        sortby = request.query_params.get('sortby')
        if sortby:
            field = sortby.rsplit(':')[0]
            if field not in self.SORT_BY_FIELDS:
                raise ValidationError(f'"sortby" field is not one of {self.SORT_BY_FIELDS}.')

        offset = int(request.query_params.get('offset', 0))
        limit = int(request.query_params.get('limit', 100))

        results = elasticsearch.get_basic_search_query(
            term=term,
            entities=(self.ENTITY_BY_NAME[entity],),
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

        if entity == 'company':
            response['companies'] = hits
        elif entity == 'contact':
            response['contacts'] = hits
        elif entity == 'investment_project':
            response['investment_projects'] = hits

        return Response(data=response)
