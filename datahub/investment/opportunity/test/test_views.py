from datetime import datetime

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.investment.opportunity.test.constants import (
    OpportunityStatus as OpportunityStatusConstant,
    OpportunityType as OpportunityTypeConstant,
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
            'description': ['This field is required.'],
            'status': ['This field is required.'],
            'type': ['This field is required.'],
            'dit_support_provided': ['This field is required.'],
        }

    def test_create_large_capital_opportunity_with_minimum_required_values(self):
        """Test creating a large capital opportunity with minimum required fields."""
        url = reverse('api-v4:large-capital-opportunity:collection')

        request_data = {
            'name': 'test',
            'description': 'Lorem ipsum',
            'type': OpportunityTypeConstant.large_capital.value.id,
            'status': OpportunityStatusConstant.seeking_investment.value.id,
            'dit_support_provided': False,
        }
        with freeze_time(datetime(2017, 4, 28, 17, 35, tzinfo=utc)):
            response = self.api_client.post(url, data=request_data)

        expected_incomplete_details_fields = [
            'opportunity_value_type',
            'opportunity_value',
            'required_checks_conducted',
            'investment_projects',
            'reasons_for_abandonment',
            'promoters',
            'lead_dit_relationship_manager',
            'other_dit_contacts',
            'total_investment_sought',
            'current_investment_secured',
        ]

        expected_incomplete_requirements_fields = [
            'investment_types',
            'estimated_return_rate',
            'time_horizons',
            'construction_risks',
            'sources_of_funding',
            'asset_classes',
        ]
        expected_incomplete_location_fields = [
            'uk_region_locations',
        ]

        response_data = response.json()
        assert 'id' in response_data
        assert response_data['incomplete_details_fields'] == expected_incomplete_details_fields
        assert (
            response_data['incomplete_requirements_fields']
            == expected_incomplete_requirements_fields
        )
        assert response_data['incomplete_location_fields'] == expected_incomplete_location_fields
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
