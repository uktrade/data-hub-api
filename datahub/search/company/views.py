from django.db.models.expressions import Case, Value, When
from django.db.models.fields import CharField
from django.db.models.functions import Cast, Concat, Upper

from datahub.company.models import Company as DBCompany
from datahub.core.query_utils import get_front_end_url_expression
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.oauth.scopes import Scope
from datahub.search.company.models import Company
from datahub.search.company.serializers import (
    AutocompleteSearchCompanySerializer,
    SearchCompanySerializer,
)
from datahub.search.views import AutocompleteSearchListAPIView, SearchAPIView, SearchExportAPIView


class SearchCompanyParams:
    """Search company parameters."""

    required_scopes = (Scope.internal_front_end,)
    entity = Company
    serializer_class = SearchCompanySerializer
    autocomplete_serializer_class = AutocompleteSearchCompanySerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }

    FILTER_FIELDS = (
        'archived',
        'description',
        'export_to_country',
        'future_interest_country',
        'global_headquarters',
        'headquarter_type',
        'name',
        'sector',
        'sector_descends',
        'country',
        'trading_address_country',
        'uk_based',
        'uk_region',
    )

    REMAP_FIELDS = {
        'export_to_country': 'export_to_countries.id',
        'future_interest_country': 'future_interest_countries.id',
        'global_headquarters': 'global_headquarters.id',
        'headquarter_type': 'headquarter_type.id',
        'sector': 'sector.id',
        'trading_address_country': 'trading_address_country.id',
        'uk_region': 'uk_region.id',
    }

    COMPOSITE_FILTERS = {
        'name': [
            'name',  # to find 2-letter words
            'name.trigram',
            'trading_names',  # to find 2-letter words
            'trading_names_trigram',
        ],
        'country': [
            'trading_address_country.id',
            'registered_address_country.id',
        ],
        'sector_descends': [
            'sector.id',
            'sector.ancestors.id',
        ],
    }


class SearchCompanyAPIView(SearchCompanyParams, SearchAPIView):
    """Filtered company search view."""


class SearchCompanyExportAPIView(SearchCompanyParams, SearchExportAPIView):
    """Company search export view."""

    queryset = DBCompany.objects.annotate(
        link=get_front_end_url_expression('company', 'pk'),
        upper_headquarter_type_name=Upper('headquarter_type__name'),
        sector_name=get_sector_name_subquery('sector'),
        # get company.turnover if set else company.turnover_range
        turnover_value=Case(
            When(
                turnover__isnull=False,
                then=Concat(Value('$'), 'turnover'),
            ),
            default='turnover_range__name',
            output_field=CharField(),
        ),
        # get company.number_of_employees if set else company.employee_range
        number_of_employees_value=Case(
            When(
                number_of_employees__isnull=False,
                then=Cast('number_of_employees', CharField()),
            ),
            default='employee_range__name',
            output_field=CharField(),
        ),
    )
    field_titles = {
        'name': 'Name',
        'link': 'Link',
        'sector_name': 'Sector',
        'registered_address_country__name': 'Country',
        'uk_region__name': 'UK region',
        'archived': 'Archived',
        'created_on': 'Date created',
        'number_of_employees_value': 'Number of employees',
        'turnover_value': 'Annual turnover',
        'upper_headquarter_type_name': 'Headquarter type',
    }


class CompanyAutocompleteSearchListAPIView(SearchCompanyParams, AutocompleteSearchListAPIView):
    """Company autocomplete search view."""

    document_fields = [
        'id',
        'name',
        'trading_name',
        'trading_names',
        'trading_address_1',
        'trading_address_2',
        'trading_address_town',
        'trading_address_county',
        'trading_address_country',
        'trading_address_postcode',
        'registered_address_1',
        'registered_address_2',
        'registered_address_town',
        'registered_address_county',
        'registered_address_country',
        'registered_address_postcode',
    ]
