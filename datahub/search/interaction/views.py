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
        'kind',
        'company',
        'company_name',
        'contact',
        'contact_name',
        'dit_adviser',
        'dit_adviser_name',
        'dit_team',
        'communication_channel',
        'investment_project',
        'service',
    )

    REMAP_FIELDS = {
        'company': 'company.id',
        'contact': 'contact.id',
        'company_name': 'company.name_trigram',
        'contact_name': 'contact.name_trigram',
        'dit_adviser': 'dit_adviser.id',
        'dit_adviser_name': 'dit_adviser.name_trigram',
        'dit_team': 'dit_team.id',
        'communication_channel': 'communication_channel.id',
        'investment_project': 'investment_project.id',
        'service': 'service.id',
    }


class SearchInteractionAPIView(SearchInteractionParams, SearchAPIView):
    """Filtered interaction search view."""

    permission_required = 'interaction.read_interaction'


class SearchInteractionExportAPIView(SearchInteractionParams, SearchExportAPIView):
    """Filtered interaction search export view."""

    permission_required = 'interaction.read_interaction'
