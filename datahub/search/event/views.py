from .models import Event
from .serializers import SearchEventSerializer
from ..views import SearchAPIView


class SearchEventAPIView(SearchAPIView):
    """Filtered event search view."""

    entity = Event
    serializer_class = SearchEventSerializer
