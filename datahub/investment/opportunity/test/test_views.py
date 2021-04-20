from datetime import datetime

import pytest
import reversion
from django.utils.timezone import now
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.constants import UKRegion as UKRegionConstant
from datahub.core.reversion import EXCLUDED_BASE_MODEL_FIELDS
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.core.test_utils import format_date_or_datetime
from datahub.investment.investor_profile.constants import (
    RequiredChecksConducted as RequiredChecksConductedConstant,
)
from datahub.investment.investor_profile.test.constants import (
    AssetClassInterest as AssetClassInterestConstant,
    ConstructionRisk as ConstructionRiskConstant,
    LargeCapitalInvestmentTypes as LargeCapitalInvestmentTypesConstant,
    ReturnRate as ReturnRateConstant,
    TimeHorizon as TimeHorizonConstant,
)
from datahub.investment.opportunity.test.factories import LargeCapitalOpportunityFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory


@pytest.fixture
def get_opportunity_for_search():
    """Sets up search list test by adding many opportunities and returning an opportunity."""
    LargeCapitalOpportunityFactory.create_batch(5)
    opportunity = LargeCapitalOpportunityFactory(
        investment_projects=[InvestmentProjectFactory()],
    )
    yield opportunity


class TestCreateLargeCapitalOpportunityView(APITestMixin):
    """Test creating a large capital opportunity."""

    def test_large_capital_unauthorized_user(self, api_client):
        """Should return 401"""
        url = reverse('api-v4:large-capital-opportunity:collection')
        user = create_test_user()
        response = api_client.get(url, user=user)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_large_capital_opportunity_fail(self):
        """Test creating a large capital opportunity without a name."""
        url = reverse('api-v4:large-capital-opportunity:collection')
        request_data = {}
        response = self.api_client.post(url, data=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'name': ['This field is required.'],
        }

    def test_create_large_capital_opportunity_with_minimum_required_values(self):
        """Test creating a large capital opportunity with minimum required fields."""
        url = reverse('api-v4:large-capital-opportunity:collection')

        request_data = {'name': 'test'}
        with freeze_time(datetime(2017, 4, 28, 17, 35, tzinfo=utc)):
            response = self.api_client.post(url, data=request_data)

        expected_incomplete_details_fields = [
            'description',
            'uk_region_locations',
            'promoters',
            'required_checks_conducted',
            'lead_dit_relationship_manager',
            'asset_classes',
            'opportunity_value',
            'construction_risks',
        ]

        expected_incomplete_requirements_fields = [
            'total_investment_sought',
            'current_investment_secured',
            'investment_types',
            'estimated_return_rate',
            'time_horizons',
        ]

        response_data = response.json()
        assert 'id' in response_data
        assert response_data['incomplete_details_fields'] == expected_incomplete_details_fields
        assert (
            response_data['incomplete_requirements_fields']
            == expected_incomplete_requirements_fields
        )
        assert response_data['created_on'] == '2017-04-28T17:35:00Z'
        assert response_data['modified_on'] == '2017-04-28T17:35:00Z'


class TestLargeCapitalOpportunityListView(APITestMixin):
    """Test large capital opportunity list view."""

    def test_large_capital_opportunity_list_view_returns_no_results_for_valid_company(self):
        """Test listing large capital opportunities without any records."""
        url = reverse('api-v4:large-capital-opportunity:collection')
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_large_capital_opportunity_list_view_invalid_search(self):
        """Test creating a large capital opportunity without an investment project."""
        url = reverse('api-v4:large-capital-opportunity:collection')
        response = self.api_client.get(
            url,
            data={'investment_projects__id': 'hello'},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {'investment_projects__id': ['Enter a valid UUID.']}

    def test_large_capital_opportunity_list_view_search_by_investment_project(
        self, get_opportunity_for_search,
    ):
        """Test searching large capital opportunity by investment project pk."""
        large_capital_opportunity = get_opportunity_for_search
        url = reverse('api-v4:large-capital-opportunity:collection')
        response = self.api_client.get(
            url,
            data={
                'investment_projects__id':
                    large_capital_opportunity.investment_projects.first().pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['investment_projects'][0]['id'] == str(
            large_capital_opportunity.investment_projects.first().pk,
        )
        assert response_data['results'][0]['id'] == str(large_capital_opportunity.pk)


class TestUpdateLargeCapitalOpportunityView(APITestMixin):
    """Test updating a large capital opportunity."""

    def test_patch_large_capital_opportunity(self):
        """Test updating a large capital opportunity."""
        new_value = 5
        opportunity = LargeCapitalOpportunityFactory()
        url = reverse('api-v4:large-capital-opportunity:item', kwargs={'pk': opportunity.pk})

        request_data = {
            'opportunity_value': new_value,
        }
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK, response_data
        assert response_data['opportunity_value'] == str(new_value)

        opportunity.refresh_from_db()
        assert opportunity.opportunity_value == new_value
        assert 'opportunity_value' not in response_data['incomplete_details_fields']

    @freeze_time('2019-05-01')
    def test_patch_large_capital_opportunity_all_details_fields(self):
        """Test updating the details fields for a large capital opportunity."""
        promoters = CompanyFactory.create_batch(2)
        lead_dit_relationship_manager = AdviserFactory()
        required_checks_conducted_by = AdviserFactory()
        opportunity = LargeCapitalOpportunityFactory()
        url = reverse('api-v4:large-capital-opportunity:item', kwargs={'pk': opportunity.pk})

        request_data = {
            'description': 'Lorem ipsum',
            'uk_region_locations': [
                {'id': UKRegionConstant.north_east.value.id},
                {'id': UKRegionConstant.north_west.value.id},
            ],
            'promoters': [{'id': promoter.pk} for promoter in promoters],
            'required_checks_conducted': {
                'id': RequiredChecksConductedConstant.cleared.value.id,
            },
            'lead_dit_relationship_manager': lead_dit_relationship_manager.pk,
            'asset_classes': [
                {'id': AssetClassInterestConstant.biofuel.value.id},
                {'id': AssetClassInterestConstant.biomass.value.id},
            ],
            'opportunity_value': 5,
            'construction_risks': [
                {
                    'id': ConstructionRiskConstant.greenfield.value.id,
                },
                {
                    'id': ConstructionRiskConstant.brownfield.value.id,
                },
            ],
            'required_checks_conducted_on': '2019-01-05',
            'required_checks_conducted_by': required_checks_conducted_by.id,
        }
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK, response_data
        assert response_data['incomplete_details_fields'] == []
        expected_uk_region_locations = {
            str(UKRegionConstant.north_east.value.id),
            str(UKRegionConstant.north_west.value.id),
        }

        assert (
            set(region['id'] for region in response_data['uk_region_locations'])
            == expected_uk_region_locations
        )
        assert (
            response_data['required_checks_conducted']['id']
            == str(RequiredChecksConductedConstant.cleared.value.id)
        )
        assert (
            response_data['lead_dit_relationship_manager']['id']
            == str(lead_dit_relationship_manager.pk)
        )
        assert (
            set(asset['id'] for asset in response_data['asset_classes'])
            == {
                str(AssetClassInterestConstant.biofuel.value.id),
                str(AssetClassInterestConstant.biomass.value.id),
            }
        )
        assert response_data['opportunity_value'] == '5'
        assert (
            set(
                construction_risk['id']
                for construction_risk in response_data['construction_risks']
            )
            == {
                str(ConstructionRiskConstant.greenfield.value.id),
                str(ConstructionRiskConstant.brownfield.value.id),
            }
        )

    @freeze_time('2019-05-01')
    def test_patch_large_capital_opportunity_all_requirements_fields(self):
        """Test updating the requirements fields for a large capital opportunity."""
        direct_investment_equity_id = (
            LargeCapitalInvestmentTypesConstant.direct_investment_in_project_equity.value.id
        )
        opportunity = LargeCapitalOpportunityFactory()
        url = reverse('api-v4:large-capital-opportunity:item', kwargs={'pk': opportunity.pk})

        request_data = {
            'total_investment_sought': 10,
            'current_investment_secured': 1,
            'investment_types': [{'id': direct_investment_equity_id}],
            'estimated_return_rate': ReturnRateConstant.up_to_five_percent.value.id,
            'time_horizons': [
                {
                    'id': TimeHorizonConstant.up_to_five_years.value.id,
                },
                {
                    'id': TimeHorizonConstant.five_to_nine_years.value.id,
                },
            ],
        }
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK, response_data
        assert response_data['incomplete_requirements_fields'] == []
        assert response_data['total_investment_sought'] == '10'
        assert response_data['current_investment_secured'] == '1'
        assert (
            response_data['investment_types'][0]['id']
            == str(direct_investment_equity_id)
        )
        assert (
            response_data['estimated_return_rate']['id']
            == str(ReturnRateConstant.up_to_five_percent.value.id)
        )
        assert (
            set(time_horizon['id'] for time_horizon in response_data['time_horizons'])
            == {
                str(TimeHorizonConstant.up_to_five_years.value.id),
                str(TimeHorizonConstant.five_to_nine_years.value.id),
            }
        )


class TestRetrieveLargeCapitalOpportunityView(APITestMixin):
    """Test retrieving a large capital opportunity."""

    @freeze_time('2019-05-01')
    def test_retrieve_large_capital_opportunity(self):
        """Test retrieving a large capital opportunity."""
        opportunity = LargeCapitalOpportunityFactory()
        url = reverse('api-v4:large-capital-opportunity:item', kwargs={'pk': opportunity.pk})

        response = self.api_client.get(url)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK, response_data

        expected_data = {
            'id': str(opportunity.pk),
            'created_on': '2019-05-01T00:00:00Z',
            'modified_on': '2019-05-01T00:00:00Z',
            'type': {
                'name': opportunity.type.name,
                'id': str(opportunity.type.pk),
            },
            'status': {
                'name': opportunity.status.name,
                'id': str(opportunity.status.pk),
            },
            'name': opportunity.name,
            'description': opportunity.description,
            'dit_support_provided': opportunity.dit_support_provided,
            'incomplete_details_fields': [
                'description',
                'uk_region_locations',
                'promoters',
                'required_checks_conducted',
                'asset_classes',
                'opportunity_value',
                'construction_risks',
            ],
            'incomplete_requirements_fields': [
                'total_investment_sought',
                'current_investment_secured',
                'investment_types',
                'estimated_return_rate',
                'time_horizons',
            ],
            'opportunity_value_type': None,
            'opportunity_value': None,
            'required_checks_conducted': None,
            'investment_projects': [],
            'reasons_for_abandonment': [],
            'promoters': [],
            'lead_dit_relationship_manager': {
                'name': opportunity.lead_dit_relationship_manager.name,
                'id': str(opportunity.lead_dit_relationship_manager.pk),
            },
            'other_dit_contacts': [],
            'total_investment_sought': None,
            'current_investment_secured': None,
            'required_checks_conducted_on': None,
            'required_checks_conducted_by': None,
            'investment_types': [],
            'estimated_return_rate': None,
            'time_horizons': [],
            'construction_risks': [],
            'sources_of_funding': [],
            'asset_classes': [],
            'uk_region_locations': [],
        }

        assert response_data == expected_data


class TestAuditLogView(APITestMixin):
    """Tests for the audit log view."""

    def test_audit_log_view(self):
        """Test retrieval of audit log."""
        initial_datetime = now()
        with reversion.create_revision():
            opportunity = LargeCapitalOpportunityFactory(
                name='This amazing opportunity',
            )

            reversion.set_comment('Initial')
            reversion.set_date_created(initial_datetime)
            reversion.set_user(self.user)

        changed_datetime = now()
        with reversion.create_revision():
            opportunity.name = 'That amazing opportunity'
            opportunity.save()

            reversion.set_comment('Changed')
            reversion.set_date_created(changed_datetime)
            reversion.set_user(self.user)

        versions = Version.objects.get_for_object(opportunity)
        version_id = versions[0].id
        url = reverse('api-v4:large-capital-opportunity:audit-item', kwargs={'pk': opportunity.pk})

        response = self.api_client.get(url)
        response_data = response.json()['results']

        # No need to test the whole response
        assert len(response_data) == 1
        entry = response_data[0]

        assert entry['id'] == version_id
        assert entry['user']['name'] == self.user.name
        assert entry['comment'] == 'Changed'
        assert entry['timestamp'] == format_date_or_datetime(changed_datetime)
        assert entry['changes']['name'] == ['This amazing opportunity', 'That amazing opportunity']
        assert not set(EXCLUDED_BASE_MODEL_FIELDS) & entry['changes'].keys()
