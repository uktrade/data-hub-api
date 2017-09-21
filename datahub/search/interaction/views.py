from datahub.oauth.scopes import Scope
from .models import Interaction
from .serializers import SearchInteractionSerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchInteractionParams:
    """Search interaction params."""

    required_scopes = (Scope.internal_front_end,)
    entity = Interaction
    serializer_class = SearchInteractionSerializer

    FILTER_FIELDS = (
        'company_name',
        'contact_name',
        'dit_adviser_name',
        'dit_team',
        'interaction_type',
        'investment_project',
        'service',
    )

    REMAP_FIELDS = {
        'company_name': 'company.name_trigram',
        'contact_name': 'contact.name_trigram',
        'dit_adviser_name': 'dit_adviser.name_trigram',
        'dit_team': 'dit_team.id',
        'interaction_type': 'interaction_type.id',
        'investment_project': 'investment_project.id',
        'service': 'service.id',
    }


class SearchInteractionAPIView(SearchInteractionParams, SearchAPIView):
    """Filtered interaction search view."""


class SearchInteractionExportAPIView(SearchInteractionParams, SearchExportAPIView):
    """Filtered interaction search export view."""
