from .models import Interaction
from .serializers import SearchInteractionSerializer
from ..views import SearchAPIView


class SearchInteractionAPIView(SearchAPIView):
    """Filtered interaction search view."""

    entity = Interaction
    serializer_class = SearchInteractionSerializer
