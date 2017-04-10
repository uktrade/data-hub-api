"""Search views."""

from django.utils.datastructures import MultiValueDictKeyError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.es.connector import ESConnector
from datahub.es.utils import format_es_results


class Search(APIView):
    """This endpoint handles the search."""

    http_method_names = ('post', )

    def post(self, request, format=None):
        """Search is a POST."""
        try:
            query_term = request.data['term']
        except (MultiValueDictKeyError, KeyError):
            raise ValidationError(detail=['Parameter "term" is mandatory.'])

        offset = request.data.get('offset', 0)
        limit = request.data.get('limit', 100)
        doc_type = request.data.get('doc_type')

        results = ESConnector().search_by_term(
            term=query_term,
            doc_type=doc_type,
            offset=int(offset),
            limit=int(limit)
        )
        formatted_results = format_es_results(results)
        return Response(data=formatted_results)
