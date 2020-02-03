import uuid
from datetime import date, datetime

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.constants import (
    Country as CountryConstant,
    UKRegion as UKRegionConstant,
)
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.investment.investor_profile.constants import (
    RequiredChecksConducted as RequiredChecksConductedConstant,
)
from datahub.investment.investor_profile.test.constants import (
    AssetClassInterest as AssetClassInterestConstant,
    ConstructionRisk as ConstructionRiskConstant,
    DealTicketSize as DealTicketSizeConstant,
    DesiredDealRole as DesiredDealRoleConstant,
    EquityPercentage as EquityPercentageConstant,
    InvestorType as InvestorTypeConstant,
    LargeCapitalInvestmentTypes as LargeCapitalInvestmentTypesConstant,
    Restriction as RestrictionConstant,
    ReturnRate as ReturnRateConstant,
    TimeHorizon as TimeHorizonConstant,
)
from datahub.investment.investor_profile.test.factories import LargeCapitalInvestorProfileFactory


INVALID_CHOICE_ERROR_MESSAGE = (
    'Select a valid choice. That choice is not one of the available choices.'
)


@pytest.fixture
def get_large_capital_profile_for_search():
    """Sets up search list test by adding many profiles and returning a large capital profile."""
    LargeCapitalInvestorProfileFactory.create_batch(5)
    investor_company = CompanyFactory()
    large_capital_profile = LargeCapitalInvestorProfileFactory(
        investor_company=investor_company,
    )
    yield large_capital_profile


class TestCreateLargeCapitalProfileView(APITestMixin):
    """Test creating a large capital profile."""

    def test_large_capital_unauthorized_user(self, api_client):
        """Should return 401"""
        url = reverse('api-v4:large-investor-profile:collection')
        user = create_test_user()
        response = api_client.get(url, user=user)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_large_capital_profile_fail(self):
        """Test creating a large capital profile without an investor company."""
        url = reverse('api-v4:large-investor-profile:collection')
        request_data = {}
        response = self.api_client.post(url, data=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'investor_company': ['This field is required.'],
        }

    def test_create_large_capital_profile_with_minimum_required_values(self):
        """Test creating a large capital profile with minimum required fields."""
        url = reverse('api-v4:large-investor-profile:collection')
        investor_company = CompanyFactory()

        request_data = {
            'investor_company': {'id': investor_company.pk},
        }
        with freeze_time(datetime(2017, 4, 28, 17, 35, tzinfo=utc)):
            response = self.api_client.post(url, data=request_data)

        expected_incomplete_details_fields = [
            'investor_type',
            'investable_capital',
            'global_assets_under_management',
            'investor_description',
            'required_checks_conducted',
        ]

        expected_incomplete_requirements_fields = [
            'deal_ticket_sizes',
            'investment_types',
            'minimum_return_rate',
            'time_horizons',
            'construction_risks',
            'minimum_equity_percentage',
            'desired_deal_roles',
            'restrictions',
            'asset_classes_of_interest',
        ]
        expected_incomplete_location_fields = [
            'uk_region_locations',
            'notes_on_locations',
            'other_countries_being_considered',
        ]

        response_data = response.json()
        assert 'id' in response_data
        assert response_data['incomplete_details_fields'] == expected_incomplete_details_fields
        assert (
            response_data['incomplete_requirements_fields']
            == expected_incomplete_requirements_fields
        )
        assert response_data['incomplete_location_fields'] == expected_incomplete_location_fields
        assert response_data['investor_company']['id'] == str(investor_company.id)
        assert response_data['created_on'] == '2017-04-28T17:35:00Z'
        assert response_data['modified_on'] == '2017-04-28T17:35:00Z'

    def test_create_large_capital_profile_fails_if_profile_already_exists(self):
        """Test creating a large investor profile with minimum required fields."""
        url = reverse('api-v4:large-investor-profile:collection')
        investor_company = CompanyFactory()
        LargeCapitalInvestorProfileFactory(
            investor_company=investor_company,
        )

        request_data = {
            'investor_company': {'id': investor_company.pk},
        }

        response = self.api_client.post(url, data=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response_data = response.json()
        assert response_data == {
            'investor_company':
                ['Investor company already has large capital investor profile'],
        }


class TestLargeCapitalProfileListView(APITestMixin):
    """Test large capital list view profile."""

    def test_large_capital_profile_list_view_returns_no_results_for_valid_company(self):
        """Test creating a large capital profile without an investor company."""
        investor_company = CompanyFactory()
        url = reverse('api-v4:large-investor-profile:collection')
        response = self.api_client.get(
            url,
            data={'investor_company_id': investor_company.pk},
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    @pytest.mark.parametrize(
        'search_parameter,expected_response',
        (
            (
                uuid.uuid4(),
                {'investor_company_id': [INVALID_CHOICE_ERROR_MESSAGE]},
            ),
            (
                'hello',
                {'investor_company_id': ['“hello” is not a valid UUID.']},
            ),
            (
                1,
                {'investor_company_id': ['“1” is not a valid UUID.']},
            ),
        ),
    )
    def test_large_capital_profile_list_view_invalid_search(
        self, search_parameter, expected_response,
    ):
        """Test creating a large capital profile without an investor company."""
        url = reverse('api-v4:large-investor-profile:collection')
        response = self.api_client.get(
            url,
            data={'investor_company_id': search_parameter},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == expected_response

    def test_large_capital_profile_list_view_search_by_investor_company(
        self, get_large_capital_profile_for_search,
    ):
        """Test searching large capital profile by investor company pk."""
        large_capital_profile = get_large_capital_profile_for_search
        url = reverse('api-v4:large-investor-profile:collection')
        response = self.api_client.get(
            url,
            data={'investor_company_id': large_capital_profile.investor_company.pk},
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['investor_company']['id'] == str(
            large_capital_profile.investor_company.pk,
        )
        assert response_data['results'][0]['id'] == str(large_capital_profile.pk)


class TestUpdateLargeCapitalProfileView(APITestMixin):
    """Test updating a large capital profile."""

    def test_patch_large_capital_profile(self):
        """Test updating a large capital profile."""
        new_description = 'Description 2'
        investor_company = CompanyFactory()
        investor_profile = LargeCapitalInvestorProfileFactory(
            investor_company=investor_company,
            investor_description='Description 1',
        )
        url = reverse('api-v4:large-investor-profile:item', kwargs={'pk': investor_profile.pk})

        request_data = {
            'investor_company': {'id': investor_company.pk},
            'investor_description': new_description,
        }
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK, response_data
        assert response_data['investor_description'] == new_description

        investor_profile.refresh_from_db()
        assert investor_profile.investor_description == new_description
        assert 'investor_description' not in response_data['incomplete_details_fields']

    def test_patch_large_capital_profile_with_a_different_company_returns_validation_error(self):
        """
        Test updating a large capital profile with a different investor company
        does return a validation error
        """
        investor_company = CompanyFactory()
        new_investor_company = CompanyFactory()
        investor_profile = LargeCapitalInvestorProfileFactory(
            investor_company=investor_company,
        )
        url = reverse('api-v4:large-investor-profile:item', kwargs={'pk': investor_profile.pk})
        request_data = {
            'investor_company': {'id': new_investor_company.pk},
        }

        response = self.api_client.patch(url, data=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response_data = response.json()
        assert response_data == {
            'investor_company':
                ['Investor company can not be updated'],
        }

    @freeze_time('2019-05-01')
    def test_patch_large_capital_profile_all_details_fields(self):
        """Test updating the details fields for a large capital profile"""
        investor_company = CompanyFactory()
        required_checks_conducted_by = AdviserFactory()
        investor_profile = LargeCapitalInvestorProfileFactory(
            investor_company=investor_company,
            required_checks_conducted_on='2017-05-01',
        )
        url = reverse('api-v4:large-investor-profile:item', kwargs={'pk': investor_profile.pk})

        request_data = {
            'investor_description': 'Description',
            'investor_type': {'id': InvestorTypeConstant.state_pension_fund.value.id},
            'investable_capital': 1000,
            'global_assets_under_management': 3000,
            'required_checks_conducted': {
                'id': RequiredChecksConductedConstant.cleared.value.id,
            },
            'required_checks_conducted_on': '2017-05-01',
            'required_checks_conducted_by': {
                'id': required_checks_conducted_by.id,
            },
        }
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK, response_data
        assert response_data['incomplete_details_fields'] == []
        assert response_data['investor_description'] == 'Description'
        assert response_data['investable_capital'] == 1000
        assert response_data['global_assets_under_management'] == 3000
        assert (
            response_data['investor_type']['id']
            == str(InvestorTypeConstant.state_pension_fund.value.id)
        )
        assert (
            response_data['required_checks_conducted']['id']
            == str(RequiredChecksConductedConstant.cleared.value.id)
        )
        assert response_data['required_checks_conducted_on'] == '2017-05-01'
        assert (
            response_data['required_checks_conducted_by']['id']
            == str(required_checks_conducted_by.id)
        )

    def test_patch_large_capital_profile_all_requirements_fields(self):
        """Test updating the requirements fields for a large capital profile."""
        direct_investment_equity_id = (
            LargeCapitalInvestmentTypesConstant.direct_investment_in_project_equity.value.id
        )

        investor_profile = LargeCapitalInvestorProfileFactory()
        url = reverse('api-v4:large-investor-profile:item', kwargs={'pk': investor_profile.pk})
        request_data = {
            'deal_ticket_sizes': [
                {'id': DealTicketSizeConstant.up_to_forty_nine_million.value.id},
            ],
            'investment_types': [
                {'id': direct_investment_equity_id},
            ],
            'minimum_return_rate': {'id': ReturnRateConstant.up_to_five_percent.value.id},
            'time_horizons': [
                {'id': TimeHorizonConstant.up_to_five_years.value.id},
                {'id': TimeHorizonConstant.five_to_nine_years.value.id},
            ],
            'construction_risks': [
                {'id': ConstructionRiskConstant.greenfield.value.id},
                {'id': ConstructionRiskConstant.brownfield.value.id},
            ],
            'minimum_equity_percentage': {'id': EquityPercentageConstant.zero_percent.value.id},
            'desired_deal_roles': [
                {'id': DesiredDealRoleConstant.lead_manager.value.id},
                {'id': DesiredDealRoleConstant.co_leader_manager.value.id},
            ],
            'restrictions': [
                {'id': RestrictionConstant.liquidity.value.id},
                {'id': RestrictionConstant.inflation_adjustment.value.id},

            ],
            'asset_classes_of_interest': [
                {'id': AssetClassInterestConstant.biofuel.value.id},
                {'id': AssetClassInterestConstant.biomass.value.id},
            ],
        }

        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK, response_data
        assert response_data['incomplete_requirements_fields'] == []
        assert (
            response_data['deal_ticket_sizes'][0]['id']
            == str(DealTicketSizeConstant.up_to_forty_nine_million.value.id)
        )
        assert response_data['investment_types'][0]['id'] == str(direct_investment_equity_id)
        assert (
            response_data['minimum_return_rate']['id']
            == str(ReturnRateConstant.up_to_five_percent.value.id)
        )
        assert (
            response_data['minimum_equity_percentage']['id']
            == str(EquityPercentageConstant.zero_percent.value.id)
        )

        expected_time_horizons = [
            TimeHorizonConstant.up_to_five_years.value.id,
            TimeHorizonConstant.five_to_nine_years.value.id,
        ]
        self._assert_many_field_ids(response_data, 'time_horizons', expected_time_horizons)

        expected_construction_risks = [
            ConstructionRiskConstant.greenfield.value.id,
            ConstructionRiskConstant.brownfield.value.id,
        ]
        self._assert_many_field_ids(
            response_data, 'construction_risks', expected_construction_risks,
        )

        expected_desired_deal_roles = [
            DesiredDealRoleConstant.lead_manager.value.id,
            DesiredDealRoleConstant.co_leader_manager.value.id,
        ]
        self._assert_many_field_ids(
            response_data, 'desired_deal_roles', expected_desired_deal_roles,
        )

        expected_restrictions = [
            RestrictionConstant.liquidity.value.id,
            RestrictionConstant.inflation_adjustment.value.id,
        ]
        self._assert_many_field_ids(
            response_data, 'restrictions', expected_restrictions,
        )

        expected_asset_classes_of_interest = [
            AssetClassInterestConstant.biofuel.value.id,
            AssetClassInterestConstant.biomass.value.id,
        ]
        self._assert_many_field_ids(
            response_data, 'asset_classes_of_interest', expected_asset_classes_of_interest,
        )

    def test_patch_large_capital_profile_all_location_fields(self):
        """Test updating the location fields for a large capital profile."""
        investor_profile = LargeCapitalInvestorProfileFactory()
        url = reverse('api-v4:large-investor-profile:item', kwargs={'pk': investor_profile.pk})
        request_data = {
            'uk_region_locations': [
                {'id': UKRegionConstant.north_east.value.id},
                {'id': UKRegionConstant.north_west.value.id},
            ],
            'other_countries_being_considered': [
                {'id': CountryConstant.ireland.value.id},
                {'id': CountryConstant.argentina.value.id},
            ],
            'notes_on_locations': 'Notes',
        }
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK, response_data
        assert response_data['incomplete_location_fields'] == []
        assert response_data['notes_on_locations'] == 'Notes'

        expected_uk_region_locations = [
            UKRegionConstant.north_east.value.id,
            UKRegionConstant.north_west.value.id,
        ]
        self._assert_many_field_ids(
            response_data, 'uk_region_locations', expected_uk_region_locations,
        )

        expected_other_countries_being_considered = [
            CountryConstant.ireland.value.id,
            CountryConstant.argentina.value.id,
        ]
        self._assert_many_field_ids(
            response_data,
            'other_countries_being_considered',
            expected_other_countries_being_considered,
        )

    def _assert_many_field_ids(self, response_data, field_name, expected_ids):
        assert len(response_data[field_name]) == len(expected_ids)
        assert (
            set([field['id'] for field in response_data[field_name]]) == set(expected_ids)
        ), field_name


@pytest.mark.django_db
class TestUpdateLargeCapitalProfileConditionalFields(APITestMixin):
    """Tests for conditional field checks when updating a large capital profile."""

    @pytest.mark.parametrize(
        'request_data,expected_status,expected_error_response',
        (
            (
                {
                    'required_checks_conducted': {
                        'id': RequiredChecksConductedConstant.cleared.value.id,
                    },
                },
                status.HTTP_400_BAD_REQUEST,
                {
                    'required_checks_conducted_on': [
                        'Enter the date of the most recent checks',
                    ],
                    'required_checks_conducted_by': [
                        'Enter the person responsible for the most recent checks',
                    ],
                },
            ),
            (
                {
                    'required_checks_conducted': {
                        'id': RequiredChecksConductedConstant.cleared.value.id,
                    },
                    'required_checks_conducted_on': '2009-09-01',
                },
                status.HTTP_400_BAD_REQUEST,
                {
                    'required_checks_conducted_on': [
                        'Date of most recent checks must be within the last 12 months',
                    ],
                    'required_checks_conducted_by': [
                        'Enter the person responsible for the most recent checks',
                    ],
                },
            ),
            (
                {
                    'required_checks_conducted': {
                        'id': RequiredChecksConductedConstant.cleared.value.id,
                    },
                    'required_checks_conducted_on': '2222-09-01',
                },
                status.HTTP_400_BAD_REQUEST,
                {
                    'required_checks_conducted_on': [
                        'Date of most recent checks must be within the last 12 months',
                    ],
                    'required_checks_conducted_by': [
                        'Enter the person responsible for the most recent checks',
                    ],
                },
            ),
            (
                {'required_checks_conducted_on': '2010-10-01'},
                status.HTTP_400_BAD_REQUEST,
                {
                    'required_checks_conducted': [
                        'Enter a value for required checks conducted',
                    ],
                },
            ),
            (
                {
                    'required_checks_conducted': {
                        'id': RequiredChecksConductedConstant.issues_identified.value.id,
                    },
                },
                status.HTTP_400_BAD_REQUEST,
                {
                    'required_checks_conducted_on': [
                        'Enter the date of the most recent checks',
                    ],
                    'required_checks_conducted_by': [
                        'Enter the person responsible for the most recent checks',
                    ],
                },
            ),
            (
                {
                    'required_checks_conducted': {
                        'id': RequiredChecksConductedConstant.not_yet_checked.value.id,
                    },
                },
                status.HTTP_200_OK,
                None,
            ),
            (
                {
                    'required_checks_conducted': {
                        'id': RequiredChecksConductedConstant.checks_not_required.value.id,
                    },
                },
                status.HTTP_200_OK,
                None,
            ),
        ),
    )
    @freeze_time('2011-01-01')
    def test_patch_large_capital_conditional_required_checks_fields(
        self, request_data, expected_status, expected_error_response,
    ):
        """Test updating the conditional required checks fields for a large capital profile."""
        investor_company = CompanyFactory()
        investor_profile = LargeCapitalInvestorProfileFactory(
            investor_company=investor_company,
        )
        url = reverse('api-v4:large-investor-profile:item', kwargs={'pk': investor_profile.pk})

        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == expected_status, response_data
        if expected_status == status.HTTP_400_BAD_REQUEST:
            assert response_data == expected_error_response
        else:
            assert (
                response_data['required_checks_conducted']['id']
                == str(request_data['required_checks_conducted']['id'])
            )

    @pytest.mark.parametrize(
        'required_checks_conducted',
        (
            RequiredChecksConductedConstant.not_yet_checked.value.id,
            RequiredChecksConductedConstant.checks_not_required.value.id,
        ),
    )
    def test_patch_large_capital_conditional_required_checks_fields_removes_old_data(
        self, required_checks_conducted,
    ):
        """Test updating the conditional required checks fields for a large capital profile."""
        investor_company = CompanyFactory()
        required_checks_conducted_by = AdviserFactory()
        investor_profile = LargeCapitalInvestorProfileFactory(
            investor_company=investor_company,
            required_checks_conducted_id=RequiredChecksConductedConstant.cleared.value.id,
            required_checks_conducted_on=date.today(),
            required_checks_conducted_by=required_checks_conducted_by,
        )
        url = reverse('api-v4:large-investor-profile:item', kwargs={'pk': investor_profile.pk})

        request_data = {
            'required_checks_conducted': {
                'id': required_checks_conducted,
            },
        }
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK, response_data

        assert (
            response_data['required_checks_conducted']['id'] == str(required_checks_conducted)
        )

        assert not response_data['required_checks_conducted_by']
        assert not response_data['required_checks_conducted_on']

    def test_patch_large_capital_required_checks_conducted_by_error(self):
        """
        Test updating required checks conducted by cannot be set when required checks
        conducted is blank.
        """
        investor_company = CompanyFactory()
        investor_profile = LargeCapitalInvestorProfileFactory(
            investor_company=investor_company,
        )
        request_data = {
            'required_checks_conducted_by': {'id': str(AdviserFactory().pk)},
        }

        url = reverse('api-v4:large-investor-profile:item', kwargs={'pk': investor_profile.pk})
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response_data
        assert response_data == {
            'required_checks_conducted': ['Enter a value for required checks conducted'],
        }

    @pytest.mark.parametrize(
        'request_data,expected_error_response',
        (
            (
                {
                    'required_checks_conducted': {
                        'id': RequiredChecksConductedConstant.issues_identified.value.id,
                    },
                },
                {
                    'required_checks_conducted_on': [
                        'Enter the date of the most recent checks',
                    ],
                    'required_checks_conducted_by': [
                        'Enter the person responsible for the most recent checks',
                    ],
                },
            ),
            (
                {
                    'required_checks_conducted': {
                        'id': RequiredChecksConductedConstant.issues_identified.value.id,
                    },
                    'required_checks_conducted_on': '2009-09-01',
                },
                {
                    'required_checks_conducted_on': [
                        'Date of most recent checks must be within the last 12 months',
                    ],
                    'required_checks_conducted_by': [
                        'Enter the person responsible for the most recent checks',
                    ],
                },
            ),
        ),
    )
    @freeze_time('2011-01-01')
    def test_patch_large_capital_required_checks_conducted_by_error_update(
        self,
        request_data,
        expected_error_response,
    ):
        """
        Test updating required checks conducted errors.

        If the value of required_checks_conducted_id is already set to a value in
        constants.REQUIRED_CHECKS_THAT_NEED_ADDITIONAL_INFORMATION and is then updated to another
        value within that same group. required_checks_conducted_on and required_checks_conducted_by
        need to be provided and the stored values ignored. When they are not or are invalid errors
        are returned.

        """
        investor_company = CompanyFactory()
        investor_profile = LargeCapitalInvestorProfileFactory(
            investor_company=investor_company,
            required_checks_conducted_id=RequiredChecksConductedConstant.cleared.value.id,
            required_checks_conducted_on=date.today(),
            required_checks_conducted_by=AdviserFactory(),
        )
        url = reverse('api-v4:large-investor-profile:item', kwargs={'pk': investor_profile.pk})
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response_data
        assert response_data == expected_error_response
