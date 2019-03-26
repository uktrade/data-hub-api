from datahub.core.query_utils import (
    get_bracketed_concat_expression,
    get_choices_as_case_expression,
    get_front_end_url_expression,
    get_full_name_expression,
    get_string_agg_subquery,
)
from datahub.interaction.models import Interaction as DBInteraction
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.oauth.scopes import Scope
from datahub.search.interaction import InteractionSearchApp
from datahub.search.interaction.serializers import SearchInteractionQuerySerializer
from datahub.search.views import register_v3_view, SearchAPIView, SearchExportAPIView


class SearchInteractionAPIViewMixin:
    """Defines common settings."""

    required_scopes = (Scope.internal_front_end,)
    search_app = InteractionSearchApp
    serializer_class = SearchInteractionQuerySerializer

    FILTER_FIELDS = (
        'kind',
        'company',
        'company_name',
        'created_on_exists',
        'dit_adviser',
        'dit_adviser_name',
        'dit_participants__adviser',
        'dit_participants__team',
        'dit_team',
        'date_after',
        'date_before',
        'communication_channel',
        'investment_project',
        'policy_areas',
        'policy_issue_types',
        'sector_descends',
        'service',
        'was_policy_feedback_provided',
    )

    REMAP_FIELDS = {
        'company': 'company.id',
        'dit_adviser': 'dit_adviser.id',
        'dit_team': 'dit_team.id',
        'dit_participants__adviser': 'dit_participants.adviser.id',
        'dit_participants__team': 'dit_participants.team.id',
        'communication_channel': 'communication_channel.id',
        'investment_project': 'investment_project.id',
        'policy_areas': 'policy_areas.id',
        'policy_issue_types': 'policy_issue_types.id',
        'service': 'service.id',
    }

    COMPOSITE_FILTERS = {
        'company_name': [
            'company.name',
            'company.name_trigram',
            'company.trading_names',  # to find 2-letter words
            'company.trading_names_trigram',
        ],
        'dit_adviser_name': [
            'dit_adviser.name',
            'dit_adviser.name_trigram',
        ],
        'sector_descends': [
            'company_sector.id',
            'company_sector.ancestors.id',
            'investment_project_sector.id',
            'investment_project_sector.ancestors.id',
        ],
    }


@register_v3_view()
class SearchInteractionAPIView(SearchInteractionAPIViewMixin, SearchAPIView):
    """Filtered interaction search view."""


@register_v3_view(sub_path='export')
class SearchInteractionExportAPIView(SearchInteractionAPIViewMixin, SearchExportAPIView):
    """Filtered interaction search export view."""

    queryset = DBInteraction.objects.annotate(
        company_link=get_front_end_url_expression('company', 'company__pk'),
        company_sector_name=get_sector_name_subquery('company__sector'),
        contact_names=get_string_agg_subquery(
            DBInteraction,
            get_full_name_expression(
                person_field_name='contacts',
                bracketed_field_name='job_title',
            ),
        ),
        adviser_names=get_string_agg_subquery(
            DBInteraction,
            get_bracketed_concat_expression(
                'dit_participants__adviser__first_name',
                'dit_participants__adviser__last_name',
                expression_to_bracket='dit_participants__team__name',
            ),
        ),
        link=get_front_end_url_expression('interaction', 'pk'),
        kind_name=get_choices_as_case_expression(DBInteraction, 'kind'),
        policy_issue_type_names=get_string_agg_subquery(
            DBInteraction,
            'policy_issue_types__name',
        ),
        policy_area_names=get_string_agg_subquery(
            DBInteraction,
            'policy_areas__name',
            # Some policy areas contain commas, so we use a semicolon to delimit multiple values
            delimiter='; ',
        ),
    )
    field_titles = {
        'date': 'Date',
        'kind_name': 'Type',
        'service__name': 'Service',
        'subject': 'Subject',
        'link': 'Link',
        'company__name': 'Company',
        'company_link': 'Company link',
        'company__address_country__name': 'Company country',
        'company__uk_region__name': 'Company UK region',
        'company_sector_name': 'Company sector',
        'contact_names': 'Contacts',
        'adviser_names': 'Advisers',
        'event__name': 'Event',
        'service_delivery_status__name': 'Service delivery status',
        'net_company_receipt': 'Net company receipt',
        'policy_issue_type_names': 'Policy issue types',
        'policy_area_names': 'Policy areas',
        'policy_feedback_notes': 'Policy feedback notes',
    }
