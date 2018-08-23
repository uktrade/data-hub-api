from django.db.models.functions import Upper

from datahub.company.models import Company as DBCompany
from datahub.core.query_utils import get_front_end_url_expression
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.oauth.scopes import Scope
from .models import Company
from .serializers import SearchCompanySerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchCompanyParams:
    """Search company parameters."""

    required_scopes = (Scope.internal_front_end,)
    entity = Company
    serializer_class = SearchCompanySerializer

    FILTER_FIELDS = (
        'account_manager',
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
        'account_manager': 'account_manager.id',
        'export_to_country': 'export_to_countries.id',
        'future_interest_country': 'future_interest_countries.id',
        'global_headquarters': 'global_headquarters.id',
        'headquarter_type': 'headquarter_type.id',
        'sector': 'sector.id',
        'trading_address_country': 'trading_address_country.id',
        'uk_region': 'uk_region.id',
    }

    COMPOSITE_FILTERS = {
        'name': ['name', 'name_trigram', 'trading_name_trigram'],
        'country': ['trading_address_country.id', 'registered_address_country.id'],
        'sector_descends': ['sector.id', 'sector.ancestors.id'],
    }


class SearchCompanyAPIView(SearchCompanyParams, SearchAPIView):
    """Filtered company search view."""


class SearchCompanyExportAPIView(SearchCompanyParams, SearchExportAPIView):
    """Company search export view."""

    queryset = DBCompany.objects.annotate(
        link=get_front_end_url_expression('company', 'pk'),
        upper_headquarter_type_name=Upper('headquarter_type__name'),
        sector_name=get_sector_name_subquery('sector'),
    )
    field_titles = {
        'name': 'Name',
        'link': 'Link',
        'sector_name': 'Sector',
        'registered_address_country__name': 'Country',
        'uk_region__name': 'UK region',
        'archived': 'Archived',
        'created_on': 'Date created',
        'employee_range__name': 'Number of employees',
        'turnover_range__name': 'Annual turnover',
        'upper_headquarter_type_name': 'Headquarter type',
    }
