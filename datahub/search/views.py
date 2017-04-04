"""Search views."""

from django.utils.datastructures import MultiValueDictKeyError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.company import models


class Search(APIView):
    """This endpoint handles the search."""

    http_method_names = ('post', )
    type_model_mapping = {'company': models.Company, 'contact': models.Contact}

    def post(self, request, format=None):
        """Search is a POST."""
        try:
            query_term = request.data['term']
        except (MultiValueDictKeyError, KeyError):
            raise ValidationError(detail=['Parameter "term" is mandatory.'])

        offset = request.data.get('offset', 0)
        limit = request.data.get('limit', 100)
        doc_type = request.data.get('doc_type')

        return Response(data='test')
