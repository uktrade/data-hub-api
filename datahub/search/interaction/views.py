from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.search import elasticsearch
from .models import Interaction
from .serializers import SearchSerializer


class SearchInteractionAPIView(APIView):
    """Filtered interaction search view."""

    http_method_names = ('post',)

    def post(self, request, format=None):
        """Performs filtered interaction search."""
        serializer = SearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        query = elasticsearch.get_search_by_entity_query(
            entity=Interaction,
            term=validated_data['original_query'],
            filters={},
            field_order=validated_data['sortby'],
            offset=validated_data['offset'],
            limit=validated_data['limit'],
        )

        results = query.execute()

        response = {
            'count': results.hits.total,
            'results': [x.to_dict() for x in results.hits],
        }

        return Response(data=response)
