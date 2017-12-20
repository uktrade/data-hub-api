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
        'created_on_exists',
        'dit_adviser',
        'dit_adviser_name',
        'dit_team',
        'date_after',
        'date_before',
        'communication_channel',
        'investment_project',
        'service',
    )

    REMAP_FIELDS = {
        'company': 'company.id',
        'contact': 'contact.id',
        'dit_adviser': 'dit_adviser.id',
        'dit_team': 'dit_team.id',
        'communication_channel': 'communication_channel.id',
        'investment_project': 'investment_project.id',
        'service': 'service.id',
    }

    COMPOSITE_FILTERS = {
        'contact_name': [
            'contact.name',
            'contact.name_trigram'
        ],
        'company_name': [
            'company.name',
            'company.name_trigram',
            'company.trading_name',
            'company.trading_name_trigram',
        ],
        'dit_adviser_name': [
            'dit_adviser.name',
            'dit_adviser.name_trigram'
        ],
    }


class SearchInteractionAPIView(SearchInteractionParams, SearchAPIView):
    """Filtered interaction search view."""


class SearchInteractionExportAPIView(SearchInteractionParams, SearchExportAPIView):
    """Filtered interaction search export view."""
