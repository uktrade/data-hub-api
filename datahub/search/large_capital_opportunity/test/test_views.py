from collections import Counter

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import (
    UKRegion as UKRegionConstant,
)
from datahub.core.test_utils import (
    APITestMixin,
)
from datahub.investment.investor_profile.test.constants import (
    AssetClassInterest as AssetClassInterestConstant,
    ConstructionRisk as ConstructionRiskConstant,
    LargeCapitalInvestmentTypes as InvestmentTypesConstant,
    ReturnRate as ReturnRateConstant,
    TimeHorizon as TimeHorizonConstant,
)
from datahub.investment.opportunity.test.constants import (
    OpportunityValueType as OpportunityValueTypeConstant,
)
from datahub.investment.opportunity.test.factories import (
    LargeCapitalOpportunityFactory,
)
from datahub.search.large_capital_opportunity import LargeCapitalOpportunitySearchApp

pytestmark = [
    pytest.mark.django_db,
    # Index objects for this search app only
    pytest.mark.es_collector_apps.with_args(LargeCapitalOpportunitySearchApp),
]


@pytest.fixture
def setup_data(es_with_collector):
    """Sets up data for the tests."""
    promoter = CompanyFactory(name='promoter')
    capital_expenditure = OpportunityValueTypeConstant.capital_expenditure.value.id
    gross_development_value = OpportunityValueTypeConstant.gross_development_value.value.id
    with freeze_time('2010-02-01'):
        frozen_created_on_opportunity = LargeCapitalOpportunityFactory(
            promoters=[CompanyFactory(
                name='Frozen promoter',
            )],
            name='Frozen project',
            description='frozen in 2010',
            construction_risks=[
                ConstructionRiskConstant.greenfield.value.id,
            ],
            total_investment_sought=1000,
            current_investment_secured=15,
            uk_region_locations=[
                UKRegionConstant.north_west.value.id,
                UKRegionConstant.east_of_england.value.id,
            ],
        )

    with freeze_time('2018-01-01 10:00:00'):
        south_project = LargeCapitalOpportunityFactory(
            promoters=[CompanyFactory(
                name='Distinct promoter',
            )],
            name='South project',
            description='South project',
            investment_types=[
                InvestmentTypesConstant.direct_investment_in_project_equity.value.id,
            ],
            total_investment_sought=6000,
            current_investment_secured=1500,
        )
    with freeze_time('2018-01-01 11:00:00'):
        north_project = LargeCapitalOpportunityFactory(
            total_investment_sought=20,
            current_investment_secured=7,
            promoters=[CompanyFactory(
                name='Another promoter',
            )],
            name='North project',
            description='North project',
            uk_region_locations=[
                UKRegionConstant.north_west.value.id,
                UKRegionConstant.north_east.value.id,
            ],
        )

    with freeze_time('2019-01-01'):
        opportunities = [
            LargeCapitalOpportunityFactory(
                name='Railway',
                description='Railway',
                promoters=[promoter],
                total_investment_sought=950,
                construction_risks=[
                    ConstructionRiskConstant.operational.value.id,
                ],
                estimated_return_rate_id=ReturnRateConstant.up_to_five_percent.value.id,
                time_horizons=[
                    TimeHorizonConstant.up_to_five_years.value.id,
                    TimeHorizonConstant.five_to_nine_years.value.id,
                ],
            ),
            LargeCapitalOpportunityFactory(
                name='Skyscraper',
                description='Skyscraper',
                promoters=[promoter],
                total_investment_sought=950,
                opportunity_value_type_id=capital_expenditure,
                opportunity_value=200,
                construction_risks=[
                    ConstructionRiskConstant.brownfield.value.id,
                ],
                time_horizons=[
                    TimeHorizonConstant.up_to_five_years.value.id,
                ],
            ),
            frozen_created_on_opportunity,
            LargeCapitalOpportunityFactory(
                name='Business centre',
                description='Business centre',
                promoters=[promoter],
                total_investment_sought=9500,
                estimated_return_rate_id=ReturnRateConstant.up_to_five_percent.value.id,
                opportunity_value_type_id=capital_expenditure,
                opportunity_value=250,
                construction_risks=[
                    ConstructionRiskConstant.brownfield.value.id,
                    ConstructionRiskConstant.greenfield.value.id,
                ],
                asset_classes=[
                    AssetClassInterestConstant.biomass.value.id,
                ],
            ),
            LargeCapitalOpportunityFactory(
                name='Restaurant',
                description='Restaurant',
                promoters=[promoter],
                total_investment_sought=9500,
                opportunity_value_type_id=gross_development_value,
                opportunity_value=200,
                asset_classes=[
                    AssetClassInterestConstant.biofuel.value.id,
                ],
                time_horizons=[
                    TimeHorizonConstant.five_to_nine_years.value.id,
                ],
            ),
            north_project,
            south_project,
        ]
    es_with_collector.flush_and_refresh()

    yield opportunities


@pytest.mark.usefixtures('setup_data')
class TestSearch(APITestMixin):
    """Tests search views."""

    def test_name_filter(self):
        """Test for name filter."""
        url = reverse('api-v4:search:large-capital-opportunity')

        response = self.api_client.post(
            url,
            data={
                'name': 'Skyscraper',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1, response.data['results']
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Skyscraper'

    def test_promoter_name_filter(self):
        """Test for in promoter name filter."""
        url = reverse('api-v4:search:large-capital-opportunity')

        response = self.api_client.post(
            url,
            data={
                'promoter_name': 'Distinct promoter',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1, response.data['results']
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['promoters'][0]['name'] == 'Distinct promoter'

    @pytest.mark.parametrize(
        'search,check_response_item,expected_results',
        (
            # Detail filters
            (
                {
                    'uk_region_location': [
                        str(UKRegionConstant.north_west.value.id),
                    ],
                },
                'name',
                ['North project', 'Frozen project'],
            ),
            (
                {
                    'asset_class': [
                        str(AssetClassInterestConstant.biofuel.value.id),
                    ],
                },
                'name',
                ['Restaurant'],
            ),
            (
                {
                    'opportunity_value_type': [
                        str(OpportunityValueTypeConstant.capital_expenditure.value.id),
                    ],
                    'opportunity_value_start': 100,
                    'opportunity_value_end': 500,
                },
                'name',
                ['Business centre', 'Skyscraper'],
            ),
            (
                {
                    'opportunity_value_type': [
                        str(OpportunityValueTypeConstant.gross_development_value.value.id),
                    ],
                    'opportunity_value_start': 100,
                    'opportunity_value_end': 500,
                },
                'name',
                ['Restaurant'],
            ),
            (
                {
                    'construction_risk': [
                        str(ConstructionRiskConstant.greenfield.value.id),
                    ],
                },
                'name',
                ['Frozen project', 'Business centre'],
            ),

            # Requirement filters
            (
                {
                    'total_investment_sought_start': 100,
                    'total_investment_sought_end': 2000,
                },
                'total_investment_sought',
                [950, 950, 1000],
            ),
            (
                {
                    'current_investment_secured_start': 10,
                    'current_investment_secured_end': 200,
                },
                'current_investment_secured',
                [15],
            ),
            (
                {
                    'investment_type': [
                        str(InvestmentTypesConstant.direct_investment_in_project_equity.value.id),
                    ],
                },
                'name',
                ['South project'],
            ),
            (
                {
                    'estimated_return_rate': [
                        str(ReturnRateConstant.up_to_five_percent.value.id),
                    ],
                },
                'name',
                ['Business centre', 'Railway'],
            ),
            (
                {
                    'time_horizon': [
                        str(TimeHorizonConstant.up_to_five_years.value.id),
                    ],
                },
                'name',
                ['Railway', 'Skyscraper'],
            ),

        ),
    )
    def test_filters(self, search, check_response_item, expected_results):
        """Test filters."""
        url = reverse('api-v4:search:large-capital-opportunity')

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
        url = reverse('api-v4:search:large-capital-opportunity')

        response = self.api_client.post(
            url,
            data={'total_investment_sought_start': 'hello'},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data == {'total_investment_sought_start': ['A valid integer is required.']}

    @pytest.mark.parametrize(
        'sort_by,check_item_key,expected_results',
        (
            (
                'name:asc',
                'name',
                [
                    'Business centre',
                    'Frozen project',
                    'North project',
                    'Railway',
                    'Restaurant',
                    'Skyscraper',
                    'South project',
                ],
            ),
            (
                'name:desc',
                'name',
                [
                    'South project',
                    'Skyscraper',
                    'Restaurant',
                    'Railway',
                    'North project',
                    'Frozen project',
                    'Business centre',
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
        url = reverse('api-v4:search:large-capital-opportunity')

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
