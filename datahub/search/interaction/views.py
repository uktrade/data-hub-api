from .models import Interaction
from .serializers import SearchInteractionSerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchInteractionParams:
    """Search interaction params."""

    entity = Interaction
    serializer_class = SearchInteractionSerializer


class SearchInteractionAPIView(SearchInteractionParams, SearchAPIView):
    """Filtered interaction search view."""


class SearchInteractionExportAPIView(SearchInteractionParams, SearchExportAPIView):
    """Filtered interaction search export view."""
