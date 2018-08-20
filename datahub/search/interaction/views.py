from datahub.core.query_utils import (
    get_choices_as_case_expression,
    get_front_end_url_expression,
    get_full_name_expression,
)
from datahub.interaction.models import Interaction as DBInteraction
from datahub.metadata.query_utils import get_sector_name_subquery
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
        company_link=get_front_end_url_expression('company', 'company__pk'),
        company_sector_name=get_sector_name_subquery('company__sector'),
        contact_name=get_full_name_expression('contact'),
        dit_adviser_name=get_full_name_expression('dit_adviser'),
        link=get_front_end_url_expression('interaction', 'pk'),
        kind_name=get_choices_as_case_expression(DBInteraction, 'kind'),
    )
    field_titles = {
        'date': 'Date',
        'kind_name': 'Type',
        'service__name': 'Service',
        'subject': 'Subject',
        'link': 'Link',
        'company__name': 'Company',
        'company_link': 'Company link',
        'company__registered_address_country__name': 'Company country',
        'company__uk_region__name': 'Company UK region',
        'company_sector_name': 'Company sector',
        'contact_name': 'Contact',
        'contact__job_title': 'Contact job title',
        'dit_adviser_name': 'Adviser',
        'dit_team__name': 'Service provider',
        'event__name': 'Event',
        'service_delivery_status__name': 'Service delivery status',
        'net_company_receipt': 'Net company receipt',
    }
