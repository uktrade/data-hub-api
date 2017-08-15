from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .. import elasticsearch


class SearchOrderAPIView(APIView):
    """Filtered order search view."""

    http_method_names = ('post',)
    DEFAULT_ORDERING = 'created_on:desc'

    def post(self, request, format=None):
        """Perform filtered order search."""
        offset = int(request.data.get('offset', 0))
        limit = int(request.data.get('limit', 100))

        results = elasticsearch.get_search_by_entity_query(
            entity=Order,
            term='',
            field_order=self.DEFAULT_ORDERING,
            offset=offset,
            limit=limit,
        ).execute()

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits]
        }

        return Response(data=response)
