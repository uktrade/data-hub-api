"""Search views."""

from rest_framework.views import APIView


class Search(APIView):
    """ View to handle the search.
    """

    http_method_names = ('get', )

    def get(self, request, format=None):
        pass
