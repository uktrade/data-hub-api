from django.db.models.expressions import Case, Value, When
from django.db.models.fields import CharField
from django.db.models.functions import Cast, Concat, Upper

from datahub.company.models import Company as DBCompany
from datahub.core.query_utils import get_front_end_url_expression
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.oauth.scopes import Scope
from datahub.search.company import CompanySearchApp
from datahub.search.company.serializers import SearchCompanyQuerySerializer
from datahub.search.views import (
    AutocompleteSearchListAPIView,
    register_v3_view,
    register_v4_view,
    SearchAPIView,
    SearchExportAPIView,
)


class SearchCompanyAPIViewMixin:
    """Defines common settings."""

    required_scopes = (Scope.internal_front_end,)
    search_app = CompanySearchApp
    serializer_class = SearchCompanyQuerySerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }

    FILTER_FIELDS = (
        'archived',
        'headquarter_type',
        'name',
        'sector_descends',
        'country',
        'uk_based',
        'uk_region',
    )

    REMAP_FIELDS = {
        'headquarter_type': 'headquarter_type.id',
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
            'address.country.id',
            'registered_address.country.id',
        ],
        'sector_descends': [
            'sector.id',
            'sector.ancestors.id',
        ],
    }


@register_v3_view()
class SearchCompanyAPIViewV3(SearchCompanyAPIViewMixin, SearchAPIView):
    """Filtered company search view V3."""

    fields_to_exclude = (
        'address',
        'registered_address',
    )


@register_v4_view()
class SearchCompanyAPIViewV4(SearchCompanyAPIViewMixin, SearchAPIView):
    """Filtered company search view V4."""

    # TODO: delete once the migration to v4 is complete
    fields_to_exclude = (
        'companies_house_data',
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
    )


@register_v3_view(sub_path='export')
@register_v4_view(sub_path='export')
class SearchCompanyExportAPIView(SearchCompanyAPIViewMixin, SearchExportAPIView):
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
        'address_country__name': 'Country',
        'uk_region__name': 'UK region',
        'archived': 'Archived',
        'created_on': 'Date created',
        'number_of_employees_value': 'Number of employees',
        'turnover_value': 'Annual turnover',
        'upper_headquarter_type_name': 'Headquarter type',
    }


@register_v3_view(sub_path='autocomplete')
class CompanyAutocompleteSearchListAPIViewV3(
    SearchCompanyAPIViewMixin,
    AutocompleteSearchListAPIView,
):
    """Company autocomplete search view V3."""

    document_fields = [
        'id',
        'name',
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


@register_v4_view(sub_path='autocomplete')
class CompanyAutocompleteSearchListAPIViewV4(
    SearchCompanyAPIViewMixin,
    AutocompleteSearchListAPIView,
):
    """Company autocomplete search view V4."""

    document_fields = [
        'id',
        'name',
        'trading_names',
        'address',
        'registered_address',
    ]
