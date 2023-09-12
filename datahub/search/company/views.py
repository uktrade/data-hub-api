from functools import reduce

from django.db.models.expressions import Case, Value, When
from django.db.models.fields import CharField
from django.db.models.functions import Cast, Concat, Upper


# from opensearch_dsl import Search

from config.settings.types import HawkScope
from datahub.company.models import Company as DBCompany, CompanyExportCountry
from datahub.core.auth import PaaSIPAuthentication
from datahub.core.constants import HeadquarterType
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.query_utils import (
    get_front_end_url_expression,
    get_string_agg_subquery,
)
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.search.company import CompanySearchApp
from datahub.search.company.serializers import (
    PublicSearchCompanyQuerySerializer,
    SearchCompanyQuerySerializer,
)
from datahub.search.views import (
    register_v4_view,
    SearchAPIView,
    SearchExportAPIView,
)


class SearchCompanyAPIViewMixin:
    """Defines common settings."""

    search_app = CompanySearchApp
    serializer_class = SearchCompanyQuerySerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }
    fields_to_exclude = (
        'uk_address_postcode',
        'uk_registered_address_postcode',
    )

    FILTER_FIELDS = (
        'id',
        'archived',
        'headquarter_type',
        'is_global_ultimate',
        'name',
        'sector_descends',
        'country',
        'area',
        'uk_based',
        'uk_region',
        'export_to_countries',
        'future_interest_countries',
        'one_list_group_global_account_manager',
        'latest_interaction_date_after',
        'latest_interaction_date_before',
        'uk_postcode',
        'export_segment',
        'export_sub_segment',
        'one_list_tier',
        'duns_number',
        'company_number',
    )

    REMAP_FIELDS = {
        'headquarter_type': 'headquarter_type.id',
        'uk_region': 'uk_region.id',
        'export_to_countries': 'export_to_countries.id',
        'future_interest_countries': 'future_interest_countries.id',
        'one_list_group_global_account_manager': 'one_list_group_global_account_manager.id',
        'one_list_tier': 'one_list_tier.id',
    }

    COMPOSITE_FILTERS = {
        'name': [
            'name',  # to find 2-letter words
            'name.trigram',
            'trading_names',  # to find 2-letter words
            'trading_names.trigram',
        ],
        'country': [
            'address.country.id',
            'registered_address.country.id',
        ],
        'sector_descends': [
            'sector.id',
            'sector.ancestors.id',
        ],
        'uk_postcode': [
            'uk_address_postcode',
            'uk_registered_address_postcode',
        ],
        'area': [
            'address.area.id',
            'registered_address.area.id',
        ],
    }


@register_v4_view()
class SearchCompanyAPIView(SearchCompanyAPIViewMixin, SearchAPIView):
    """Filtered company search view."""

    def deep_get(self, dictionary, keys, default=None):
        """
        Perform a deep search on a dictionary to find the item at the location provided in the keys
        """
        return reduce(
            lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
            keys.split('|'),
            dictionary,
        )

    def get_base_query(self, request, validated_data):
        base_query = super().get_base_query(request, validated_data)

        raw_query = base_query.to_dict()
        filters = self.deep_get(raw_query, 'query|bool|filter')
        if not filters:
            return base_query

        filter_index = None
        for index, filter in enumerate(filters):
            if filter.get('bool'):
                filter_index = index
                break

        if filter_index is None:
            return base_query

        must_filters = filters[filter_index]['bool']['must']
        for index, filter in enumerate(must_filters):
            # By default the logic to generate an opensearch query inside get_base_query uses an
            # and for each column passed to it. In this use case, when we detect a query for the
            # ghq headquarter id we add an addiitonal should entry into the should array
            should_queries = self.deep_get(filter, 'bool|should')

            if should_queries:
                for should_query in should_queries:
                    if (
                        self.deep_get(should_query, 'match|headquarter_type.id|query')
                        == HeadquarterType.ghq.value.id
                    ):
                        should_queries.append(
                            {
                                'match': {
                                    'is_global_ultimate': {
                                        'query': True,
                                    },
                                },
                            },
                        )
                        break
                raw_query['query']['bool']['filter'][filter_index]['bool']['must'][index]['bool'][
                    'should'
                ] = should_queries

#        return Search.from_dict(raw_query)
        base_query.raw_query = raw_query
        return base_query


@register_v4_view(is_public=True)
class PublicSearchCompanyAPIView(HawkResponseSigningMixin, SearchAPIView):
    """
    Company search view using Hawk authentication.

    This is a slightly stripped down version of the company search view, intended for use by the
    Market Access service using Hawk authentication and without a user context in requests.

    Some fields containing personal data are deliberately omitted.
    """

    search_app = CompanySearchApp
    serializer_class = PublicSearchCompanyQuerySerializer
    authentication_classes = (PaaSIPAuthentication, HawkAuthentication)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.public_company
    fields_to_include = (
        'id',
        'address',
        'archived',
        'archived_on',
        'archived_reason',
        'business_type',
        'company_number',
        'created_on',
        'description',
        'duns_number',
        'employee_range',
        'export_experience_category',
        'export_to_countries',
        'future_interest_countries',
        'global_headquarters',
        'headquarter_type',
        'is_global_ultimate',
        'modified_on',
        'name',
        'reference_code',
        'registered_address',
        'sector',
        'trading_names',
        'turnover_range',
        'uk_based',
        'uk_region',
        'vat_number',
        'website',
        'export_segment',
        'export_sub_segment',
    )

    FILTER_FIELDS = (
        'archived',
        'name',
    )

    COMPOSITE_FILTERS = {
        'name': [
            'name',  # to find 2-letter words
            'name.trigram',
            'trading_names',  # to find 2-letter words
            'trading_names.trigram',
        ],
    }


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
        export_to_countries_list=get_string_agg_subquery(
            DBCompany,
            Case(
                When(
                    export_countries__status=CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                    then=Cast('export_countries__country__name', CharField()),
                ),
            ),
        ),
        future_interest_countries_list=get_string_agg_subquery(
            DBCompany,
            Case(
                When(
                    export_countries__status=CompanyExportCountry.Status.FUTURE_INTEREST,
                    then=Cast('export_countries__country__name', CharField()),
                ),
            ),
        ),
    )

    @property
    def field_titles(self):
        """
        Returns field titles for CSV export

        There is implicit ordering here, guaranteed for python >= 3.7 to be insertion order
        This is a property because we don't want it to evaluate prior to database instantiation
        """
        field_titles = {
            'name': 'Name',
            'link': 'Link',
            'sector_name': 'Sector',
            'address_country__name': 'Country',
        }

        field_titles.update(
            {
                'address_area__name': 'Area',
                'uk_region__name': 'UK region',
                'export_to_countries_list': 'Countries exported to',
                'future_interest_countries_list': 'Countries of interest',
                'archived': 'Archived',
                'created_on': 'Date created',
                'number_of_employees_value': 'Number of employees',
                'turnover_value': 'Annual turnover',
                'upper_headquarter_type_name': 'Headquarter type',
            },
        )
        return field_titles
