from django.db.models import Case, F, Max, Value, When

from datahub.company.models import Contact as DBContact
from datahub.core.query_utils import (
    ConcatWS,
    get_aggregate_subquery,
    get_front_end_url_expression,
    get_full_name_expression,
    get_top_related_expression_subquery,
    NullIf,
)
from datahub.interaction.models import Interaction as DBInteraction
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.oauth.scopes import Scope
from datahub.search.contact.models import Contact
from datahub.search.contact.serializers import SearchContactSerializer
from datahub.search.views import SearchAPIView, SearchExportAPIView


class SearchContactParams:
    """Search contact params."""

    required_scopes = (Scope.internal_front_end,)
    entity = Contact
    serializer_class = SearchContactSerializer
    es_sort_by_remappings = {
        'first_name': 'first_name.keyword',
        'last_name': 'last_name.keyword',
        'name': 'name.keyword',
    }

    FILTER_FIELDS = (
        'name',
        'company',
        'company_name',
        'company_sector',
        'company_sector_descends',
        'company_uk_region',
        'created_by',
        'created_on_exists',
        'address_country',
        'archived',
    )

    REMAP_FIELDS = {
        'company': 'company.id',
        'company_sector': 'company_sector.id',
        'company_uk_region': 'company_uk_region.id',
        'address_country': 'address_country.id',
        'created_by': 'created_by.id',
    }

    COMPOSITE_FILTERS = {
        'name': [
            'name',
            'name.trigram',
        ],
        'company_name': [
            'company.name',
            'company.name_trigram',
            'company.trading_names',  # to find 2-letter words
            'company.trading_names_trigram',
        ],
        'company_sector_descends': [
            'company_sector.id',
            'company_sector.ancestors.id',
        ],
    }


class SearchContactAPIView(SearchContactParams, SearchAPIView):
    """Filtered contact search view."""


class SearchContactExportAPIView(SearchContactParams, SearchExportAPIView):
    """Company search export view."""

    db_sort_by_remappings = {
        'address_country.name': 'computed_country_name',
    }
    queryset = DBContact.objects.annotate(
        name=get_full_name_expression(),
        link=get_front_end_url_expression('contact', 'pk'),
        company_sector_name=get_sector_name_subquery('company__sector'),
        company_link=get_front_end_url_expression('company', 'company__pk'),
        computed_country_name=Case(
            When(address_same_as_company=True, then='company__registered_address_country__name'),
            default='address_country__name',
        ),
        computed_postcode=Case(
            When(address_same_as_company=True, then='company__registered_address_postcode'),
            default='address_postcode',
        ),
        full_telephone_number=ConcatWS(
            Value(' '),
            NullIf('telephone_countrycode', Value('')),
            NullIf('telephone_number', Value('')),
        ),
        date_of_latest_interaction=get_aggregate_subquery(
            DBContact,
            Max('interactions__date'),
        ),
        team_of_latest_interaction=get_top_related_expression_subquery(
            DBInteraction.contacts.field,
            F('dit_team__name'),
            ('-date',),
        ),
    )
    field_titles = {
        'name': 'Name',
        'job_title': 'Job title',
        'created_on': 'Date created',
        'archived': 'Archived',
        'link': 'Link',
        'company__name': 'Company',
        'company_sector_name': 'Company sector',
        'company_link': 'Company link',
        'company__uk_region__name': 'Company UK region',
        'computed_country_name': 'Country',
        'computed_postcode': 'Postcode',
        'full_telephone_number': 'Phone number',
        'email': 'Email address',
        'accepts_dit_email_marketing': 'Accepts DIT email marketing',
        'date_of_latest_interaction': 'Date of latest interaction',
        'team_of_latest_interaction': 'Team of latest interaction',
        'created_by__dit_team__name': 'Created by team',
    }
