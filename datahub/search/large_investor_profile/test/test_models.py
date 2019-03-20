import pytest

from datahub.investment.investor_profile.test.factories import LargeInvestorProfileFactory
from datahub.search.large_investor_profile.models import (
    LargeInvestorProfile as ESLargeInvestorProfile,
)

pytestmark = pytest.mark.django_db


class TestLargeInvestorProfileElasticModel:
    """Test for the large investor profile elasticsearch model"""

    def test_large_investor_profile_dbmodel_to_dict(self, setup_es):
        """Tests conversion of db model to dict."""
        large_investor_profile = LargeInvestorProfileFactory()

        result = ESLargeInvestorProfile.db_object_to_dict(large_investor_profile)
        keys = {
            'asset_classes_of_interest',
            'construction_risks',
            'country_of_origin',
            'created_by',
            'created_on',
            'deal_ticket_sizes',
            'desired_deal_roles',
            'global_assets_under_management',
            'id',
            'investable_capital',
            'investment_types',
            'investor_company',
            'investor_description',
            'investor_type',
            'minimum_equity_percentage',
            'minimum_return_rate',
            'modified_on',
            'notes_on_locations',
            'other_countries_being_considered',
            'required_checks_conducted',
            'restrictions',
            'time_horizons',
            'uk_region_locations',
        }
        assert set(result.keys()) == keys

    def test_investment_project_dbmodels_to_es_documents(self, setup_es):
        """Tests conversion of db models to Elasticsearch documents."""
        large_profiles = LargeInvestorProfileFactory.create_batch(2)

        result = ESLargeInvestorProfile.db_objects_to_es_documents(large_profiles)

        assert len(list(result)) == len(large_profiles)
