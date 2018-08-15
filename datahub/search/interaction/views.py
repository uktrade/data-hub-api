from django.db.models import Value
from django.db.models.functions import Concat

from datahub.interaction.models import Interaction as DBInteraction
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
        'sector_descends',
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
        'sector_descends': [
            'company_sector.id',
            'company_sector.ancestors.id',
            'investment_project_sector.id',
            'investment_project_sector.ancestors.id',
        ],
    }


class SearchInteractionAPIView(SearchInteractionParams, SearchAPIView):
    """Filtered interaction search view."""


class SearchInteractionExportAPIView(SearchInteractionParams, SearchExportAPIView):
    """Filtered interaction search export view."""

    queryset = DBInteraction.objects.annotate(
        dit_adviser_name=Concat('dit_adviser__first_name', Value(' '), 'dit_adviser__last_name'),
    )
    field_titles = {
        'date': 'Date',
        'company__name': 'Company',
        'service__name': 'Service',
        'subject': 'Subject',
        'dit_adviser_name': 'Adviser',
        'dit_team__name': 'Service provider',
    }
