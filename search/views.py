"""Search views."""

from rest_framework.views import APIView


class Search(APIView):
    """ View to handle the search.
    """

    def get(self, request, format=None):
        pass
