from cgi import parse_header
from collections import Counter
from csv import DictReader
from io import StringIO

import pytest
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, TeamFactory
from datahub.core.constants import (
    Country as CountryConstant,
    UKRegion as UKRegionConstant,
)
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_csv_data,
    get_attr_or_none,
    join_attr_values,
)
from datahub.investment.investor_profile.models import LargeCapitalInvestorProfile
from datahub.investment.investor_profile.permissions import InvestorProfilePermission
from datahub.investment.investor_profile.test.constants import (
    AssetClassInterest as AssetClassInterestConstant,
    ConstructionRisk as ConstructionRiskConstant,
    DealTicketSize as DealTicketSizeConstant,
    DesiredDealRole as DesiredDealRoleConstant,
    EquityPercentage as EquityPercentageConstant,
    LargeCapitalInvestmentTypes as InvestmentTypesConstant,
    Restriction as RestrictionConstant,
    ReturnRate as ReturnRateConstant,
    TimeHorizon as TimeHorizonConstant,
)
from datahub.investment.investor_profile.test.factories import (
    CompleteLargeCapitalInvestorProfileFactory,
    LargeCapitalInvestorProfileFactory,
)
from datahub.search.large_investor_profile import LargeInvestorProfileSearchApp
from datahub.search.large_investor_profile.views import SearchLargeInvestorProfileExportAPIView

pytestmark = [
    pytest.mark.django_db,
    # Index objects for this search app only
    pytest.mark.es_collector_apps.with_args(LargeInvestorProfileSearchApp),
]


@pytest.fixture
def setup_data(es_with_collector):
    """Sets up data for the tests."""
    investor_company = CompanyFactory(name='large abcdef')
    argentina_investor_company = CompanyFactory(
        name='argentina plc',
        address_country_id=CountryConstant.argentina.value.id,
    )
    with freeze_time('2010-02-01'):
        frozen_created_on_profile = LargeCapitalInvestorProfileFactory(
            investor_company=CompanyFactory(
                name='Frozen limited',
            ),
            investor_description='frozen in 2010',
            construction_risks=[
                ConstructionRiskConstant.greenfield.value.id,
            ],
            desired_deal_roles=[
                DesiredDealRoleConstant.lead_manager.value.id,
            ],
            minimum_equity_percentage_id=EquityPercentageConstant.zero_percent.value.id,
            investable_capital=0,
            global_assets_under_management=10,
            uk_region_locations=[
                UKRegionConstant.north_west.value.id,
                UKRegionConstant.east_of_england.value.id,
            ],
        )
    with freeze_time('2018-01-01 10:00:00'):
        south_project = LargeCapitalInvestorProfileFactory(
            investor_company=CompanyFactory(
                name='South',
            ),
            investor_description='South Project',
            investment_types=[
                InvestmentTypesConstant.direct_investment_in_project_equity.value.id,
            ],
            global_assets_under_management=60,
        )
    with freeze_time('2018-01-01 11:00:00'):
        north_project = LargeCapitalInvestorProfileFactory(
            investable_capital=20,
            investor_company=CompanyFactory(
                name='North',
            ),
            investor_description='North Project',
            uk_region_locations=[
                UKRegionConstant.north_west.value.id,
                UKRegionConstant.north_east.value.id,
            ],
            other_countries_being_considered=[
                CountryConstant.ireland.value.id,
                CountryConstant.canada.value.id,
            ],
            global_assets_under_management=70,
        )

    with freeze_time('2019-01-01'):
        investor_profiles = [
            LargeCapitalInvestorProfileFactory(
                investor_description='Operational construction',
                investor_company=investor_company,
                investable_capital=950,
                construction_risks=[
                    ConstructionRiskConstant.operational.value.id,
                ],
                minimum_return_rate_id=ReturnRateConstant.up_to_five_percent.value.id,
                time_horizons=[
                    TimeHorizonConstant.up_to_five_years.value.id,
                    TimeHorizonConstant.five_to_nine_years.value.id,
                ],
                global_assets_under_management=20,
            ),
            LargeCapitalInvestorProfileFactory(
                investor_description='Argentina project',
                investor_company=argentina_investor_company,
                investable_capital=1490,
                construction_risks=[
                    ConstructionRiskConstant.brownfield.value.id,
                ],
                time_horizons=[
                    TimeHorizonConstant.up_to_five_years.value.id,
                ],
                restrictions=[
                    RestrictionConstant.inflation_adjustment.value.id,
                ],
                global_assets_under_management=30,
            ),
            frozen_created_on_profile,
            LargeCapitalInvestorProfileFactory(
                investor_company=CompanyFactory(
                    address_country_id=CountryConstant.argentina.value.id,
                    name='2 constructions ltd',
                ),
                investor_description='2 construction risks',
                construction_risks=[
                    ConstructionRiskConstant.brownfield.value.id,
                    ConstructionRiskConstant.greenfield.value.id,
                ],
                investable_capital=3000,
                asset_classes_of_interest=[
                    AssetClassInterestConstant.biomass.value.id,
                ],
                restrictions=[
                    RestrictionConstant.inflation_adjustment.value.id,
                ],
                global_assets_under_management=40,
            ),
            LargeCapitalInvestorProfileFactory(
                investor_company=CompanyFactory(
                    name='Deal up ltd',
                ),
                investable_capital=10,
                investor_description='Deal up',
                deal_ticket_sizes=[
                    DealTicketSizeConstant.up_to_forty_nine_million.value.id,
                ],
                asset_classes_of_interest=[
                    AssetClassInterestConstant.biofuel.value.id,
                ],
                time_horizons=[
                    TimeHorizonConstant.five_to_nine_years.value.id,
                ],
                restrictions=[
                    RestrictionConstant.liquidity.value.id,
                ],
                minimum_equity_percentage_id=EquityPercentageConstant.zero_percent.value.id,
                global_assets_under_management=50,
            ),
            north_project,
            south_project,
        ]
    es_with_collector.flush_and_refresh()

    yield investor_profiles


@pytest.mark.usefixtures('setup_data')
class TestSearch(APITestMixin):
    """Tests search views."""

    def test_investor_company_name_filter(self):
        """Test for in investor company name filter."""
        url = reverse('api-v4:search:large-investor-profile')

        response = self.api_client.post(
            url,
            data={
                'investor_company_name': 'large',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1, response.data['results']
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['investor_company']['name'] == 'large abcdef'

    @pytest.mark.parametrize(
        'country,number_of_results',
        (
            (CountryConstant.argentina, 2),
            (CountryConstant.ireland, 0),
        ),
    )
    def test_country_of_origin_filter(self, country, number_of_results):
        """Test for country of origin filter."""
        url = reverse('api-v4:search:large-investor-profile')

        response = self.api_client.post(
            url,
            data={
                'country_of_origin': [str(country.value.id)],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == number_of_results, response.data['results']
        assert len(response.data['results']) == number_of_results
        assert Counter(
            result['country_of_origin']['name'] for result in response.data['results']
        ) == Counter(
            [country.value.name] * number_of_results,
        )

    @pytest.mark.parametrize(
        'search,check_response_item,expected_results',
        (
            (
                {
                    'investable_capital_start': 1000,
                    'investable_capital_end': 2000,
                },
                'investable_capital',
                [1490],

            ),
            (
                {
                    'investable_capital_start': 1000,
                },
                'investable_capital',
                [1490, 3000],
            ),
            (
                {
                    'investable_capital_start': 10000,
                },
                'investable_capital',
                [],
            ),
            (
                {
                    'investable_capital_end': 10000,
                },
                'investable_capital',
                [0, 10, 20, 950, 1490, 3000],
            ),
            (
                {
                    'global_assets_under_management_start': 30,
                    'global_assets_under_management_end': 50,
                },
                'global_assets_under_management',
                [30, 40, 50],
            ),
            (
                {
                    'construction_risk': [
                        str(ConstructionRiskConstant.brownfield.value.id),
                        str(ConstructionRiskConstant.operational.value.id),
                    ],
                },
                'investor_description',
                ['2 construction risks', 'Argentina project', 'Operational construction'],
            ),
            (
                {
                    'minimum_return_rate': [
                        str(ReturnRateConstant.up_to_five_percent.value.id),
                    ],
                },
                'investor_description',
                ['Operational construction'],
            ),
            (
                {
                    'created_on_after': '2010-01-01',
                    'created_on_before': '2011-01-01',
                },
                'created_on',
                ['2010-02-01T00:00:00+00:00'],
            ),
            (
                {
                    'created_on_after': '2020-01-01',
                },
                'created_on',
                [],
            ),
            (
                {
                    'deal_ticket_size': [
                        str(DealTicketSizeConstant.up_to_forty_nine_million.value.id),
                    ],
                },
                'investor_description',
                ['Deal up'],
            ),
            (
                {
                    'asset_classes_of_interest': [
                        str(AssetClassInterestConstant.biomass.value.id),
                    ],
                },
                'investor_description',
                ['2 construction risks'],
            ),
            (
                {
                    'time_horizon': [
                        str(TimeHorizonConstant.five_to_nine_years.value.id),
                    ],
                },
                'investor_description',
                ['Operational construction', 'Deal up'],
            ),
            (
                {
                    'restriction': [
                        str(RestrictionConstant.inflation_adjustment.value.id),
                    ],
                },
                'investor_description',
                ['Argentina project', '2 construction risks'],
            ),
            (
                {
                    'desired_deal_role': [
                        str(DesiredDealRoleConstant.co_leader_manager.value.id),
                    ],
                },
                'investor_description',
                [],
            ),
            (
                {
                    'desired_deal_role': [
                        str(DesiredDealRoleConstant.lead_manager.value.id),
                    ],
                },
                'investor_description',
                ['frozen in 2010'],
            ),
            (
                {
                    'minimum_equity_percentage': [
                        str(EquityPercentageConstant.zero_percent.value.id),
                    ],
                },
                'investor_description',
                ['Deal up', 'frozen in 2010'],
            ),
            (
                {
                    'other_countries_being_considered': [
                        str(CountryConstant.canada.value.id),
                        str(CountryConstant.anguilla.value.id),
                    ],
                },
                'investor_description',
                ['North Project'],
            ),
            (
                {
                    'uk_region_location': [
                        str(UKRegionConstant.north_west.value.id),
                    ],
                },
                'investor_description',
                ['frozen in 2010', 'North Project'],
            ),

        ),
    )
    def test_filters(self, search, check_response_item, expected_results):
        """Test filters."""
        url = reverse('api-v4:search:large-investor-profile')

        response = self.api_client.post(
            url,
            data=search,
        )

        assert response.status_code == status.HTTP_200_OK
        expected_number_of_results = len(expected_results)
        assert response.data['count'] == expected_number_of_results, response.data['results']
        assert len(response.data['results']) == expected_number_of_results
        assert (
            Counter(result[check_response_item] for result in response.data['results'])
            == Counter(expected_results)
        )

    def test_investable_capital_filter_error(self):
        """Test investable capital filter error."""
        url = reverse('api-v4:search:large-investor-profile')

        response = self.api_client.post(
            url,
            data={'investable_capital_start': 'hello'},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data == {'investable_capital_start': ['A valid integer is required.']}

    @pytest.mark.parametrize(
        'sort_by,check_item_key,expected_results',
        (
            (
                'investable_capital:desc',
                'investable_capital',
                [
                    3000,
                    1490,
                    950,
                    20,
                    10,
                    0,
                    None,
                ],
            ),
            (
                'investable_capital:asc',
                'investable_capital',
                [
                    None,
                    0,
                    10,
                    20,
                    950,
                    1490,
                    3000,
                ],
            ),
            (
                'global_assets_under_management:asc',
                'global_assets_under_management',
                [
                    10,
                    20,
                    30,
                    40,
                    50,
                    60,
                    70,
                ],
            ),
            (
                'global_assets_under_management:desc',
                'global_assets_under_management',
                [
                    70,
                    60,
                    50,
                    40,
                    30,
                    20,
                    10,
                ],
            ),
            (
                'investor_company.name:asc',
                'investor_company__name',
                [
                    '2 constructions ltd',
                    'argentina plc',
                    'Deal up ltd',
                    'Frozen limited',
                    'large abcdef',
                    'North',
                    'South',
                ],
            ),
            (
                'investor_company.name:desc',
                'investor_company__name',
                [
                    'South',
                    'North',
                    'large abcdef',
                    'Frozen limited',
                    'Deal up ltd',
                    'argentina plc',
                    '2 constructions ltd',
                ],
            ),
            (
                'modified_on:asc',
                'modified_on',
                [
                    '2010-02-01T00:00:00+00:00',
                    '2018-01-01T10:00:00+00:00',
                    '2018-01-01T11:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                ],
            ),
            (
                'modified_on:desc',
                'modified_on',
                [
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2018-01-01T11:00:00+00:00',
                    '2018-01-01T10:00:00+00:00',
                    '2010-02-01T00:00:00+00:00',
                ],
            ),
            (
                'created_on:asc',
                'created_on',
                [
                    '2010-02-01T00:00:00+00:00',
                    '2018-01-01T10:00:00+00:00',
                    '2018-01-01T11:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                ],
            ),
            (
                'created_on:desc',
                'created_on',
                [
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2019-01-01T00:00:00+00:00',
                    '2018-01-01T11:00:00+00:00',
                    '2018-01-01T10:00:00+00:00',
                    '2010-02-01T00:00:00+00:00',
                ],
            ),

        ),
    )
    def test_sorts(self, sort_by, check_item_key, expected_results):
        """Test search sorts."""
        url = reverse('api-v4:search:large-investor-profile')

        response = self.api_client.post(
            url,
            data={'sortby': sort_by},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 7, response.data['results']
        actual_results = [
            self._get_data_item(result, check_item_key) for result in response.data['results']
        ]
        assert expected_results == actual_results

    def _get_data_item(self, result, check_item_key):
        check_item_key_list = check_item_key.split('__')
        item = None
        for key in check_item_key_list:
            item = item[key] if item else result[key]
        return item


class TestLargeInvestorProfileExportView(APITestMixin):
    """Tests large capital investor profile export view."""

    @pytest.mark.parametrize(
        'permissions,expected_status_code',
        (
            (
                (),
                status.HTTP_403_FORBIDDEN,
            ),
            (
                (
                    InvestorProfilePermission.view_investor_profile,
                ),
                status.HTTP_403_FORBIDDEN,
            ),
            (
                (
                    InvestorProfilePermission.export,
                ),
                status.HTTP_403_FORBIDDEN,
            ),
            (
                (
                    InvestorProfilePermission.view_investor_profile,
                    InvestorProfilePermission.export,
                ),
                status.HTTP_200_OK,
            ),
        ),
    )
    def test_user_needs_correct_permissions_to_export_data(
        self, es, permissions, expected_status_code,
    ):
        """Test that a user without the correct permissions cannot export data."""
        user = create_test_user(dit_team=TeamFactory(), permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:search:large-investor-profile-export')
        response = api_client.post(url)
        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        'request_sortby,orm_ordering',
        (
            ('created_on:desc', '-created_on'),
            ('modified_on:desc', '-modified_on'),
            ('investable_capital:asc', 'investable_capital'),
            ('global_assets_under_management:desc', '-global_assets_under_management'),
            ('investor_company.name', 'investor_company__name'),
        ),
    )
    def test_export(self, es_with_collector, request_sortby, orm_ordering):
        """Test export large capital investor profile search results."""
        url = reverse('api-v4:search:large-investor-profile-export')

        CompleteLargeCapitalInvestorProfileFactory(
            investable_capital=10000,
            global_assets_under_management=20000,
        )
        with freeze_time('2018-01-01 11:12:13'):
            LargeCapitalInvestorProfileFactory(
                investable_capital=300,
                global_assets_under_management=200,
            )

        es_with_collector.flush_and_refresh()

        data = {}
        if request_sortby:
            data['sortby'] = request_sortby

        with freeze_time('2018-01-01 11:12:13'):
            response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert parse_header(response.get('Content-Disposition')) == (
            'attachment', {
                'filename': 'Data Hub - Large capital profiles - 2018-01-01-11-12-13.csv',
            },
        )

        sorted_profiles = LargeCapitalInvestorProfile.objects.order_by(orm_ordering, 'pk')
        response_text = response.getvalue().decode('utf-8-sig')
        reader = DictReader(StringIO(response_text))

        assert reader.fieldnames == list(
            SearchLargeInvestorProfileExportAPIView.field_titles.values(),
        )

        expected_row_data = [
            {
                'Date created': profile.created_on,
                'Global assets under management': profile.global_assets_under_management,
                'Investable capital': profile.investable_capital,
                'Investor company': get_attr_or_none(
                    profile, 'investor_company.name',
                ),
                'Investor description': profile.investor_description,
                'Notes on locations': profile.notes_on_locations,
                'Investor type': get_attr_or_none(
                    profile, 'investor_type.name',
                ),
                'Required checks conducted': get_attr_or_none(
                    profile, 'required_checks_conducted.name',
                ),
                'Minimum return rate': get_attr_or_none(
                    profile, 'minimum_return_rate.name',
                ),
                'Minimum equity percentage': get_attr_or_none(
                    profile, 'minimum_equity_percentage.name',
                ),
                'Date last modified': profile.modified_on,
                'UK regions of interest': join_attr_values(
                    profile.uk_region_locations.order_by('name'),
                ),
                'Restrictions': join_attr_values(
                    profile.restrictions.order_by('name'),
                ),
                'Time horizons': join_attr_values(
                    profile.time_horizons.order_by('name'),
                ),
                'Investment types': join_attr_values(
                    profile.investment_types.order_by('name'),
                ),
                'Deal ticket sizes': join_attr_values(
                    profile.deal_ticket_sizes.order_by('name'),
                ),
                'Desired deal roles': join_attr_values(
                    profile.desired_deal_roles.order_by('name'),
                ),
                'Required checks conducted by': get_attr_or_none(
                    profile, 'required_checks_conducted_by.name',
                ),
                'Required checks conducted on': profile.required_checks_conducted_on,
                'Other countries being considered': join_attr_values(
                    profile.other_countries_being_considered.order_by('name'),
                ),
                'Construction risks': join_attr_values(
                    profile.construction_risks.order_by('name'),
                ),
                'Data Hub profile reference': str(profile.pk),
                'Asset classes of interest': join_attr_values(
                    profile.asset_classes_of_interest.order_by('name'),
                ),
                'Data Hub link': (
                    f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["company"]}'
                    f'/{profile.investor_company.pk}/investments/large-capital-profile'
                ),
            }
            for profile in sorted_profiles
        ]

        expected_rows = format_csv_data(expected_row_data)

        # item is an ordered dict so is cast to a dict to make the comparison easier to
        # interpret in the event of the assert actual_rows == expected_rows failing.
        actual_rows = [dict(item) for item in reader]

        assert actual_rows == expected_rows
