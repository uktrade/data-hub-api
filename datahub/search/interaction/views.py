from datahub.oauth.scopes import Scope
from .models import Interaction
from .serializers import SearchInteractionSerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchInteractionParams:
    """Search interaction params."""

    required_scopes = (Scope.internal_front_end,)
    entity = Interaction
    serializer_class = SearchInteractionSerializer


class SearchInteractionAPIView(SearchInteractionParams, SearchAPIView):
    """Filtered interaction search view."""


class SearchInteractionExportAPIView(SearchInteractionParams, SearchExportAPIView):
    """Filtered interaction search export view."""
