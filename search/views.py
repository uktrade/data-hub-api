"""Search views."""

from django.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import get_elasticsearch_client

from .utils import search_by_term


class Search(APIView):
    """ View to handle the search."""

    http_method_names = ('post', )

    def post(self, request, format=None):
        query_term = request.POST['term']
        offset = request.POST.get('offset', 0)
        limit = request.POST.get('limit', 100)
        client = get_elasticsearch_client()
        results = search_by_term(
            client=client,
            index=settings.ES_INDEX,
            term=query_term,
            offset=int(offset),
            limit=int(limit)
        )
        return Response(data=results.hits.hits)
