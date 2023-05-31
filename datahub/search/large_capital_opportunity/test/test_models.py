import pytest

from datahub.investment.opportunity.test.factories import LargeCapitalOpportunityFactory
from datahub.search.large_capital_opportunity.models import (
    LargeCapitalOpportunity as SearchLargeCapitalOpportunity,
)

pytestmark = pytest.mark.django_db


class TestLargeCapitalOpportunitySearchModel:
    """Test for the large capital opportunity OpenSearch model"""

    def test_large_capital_opportunity_dbmodel_to_dict(self, opensearch):
        """Tests conversion of db model to dict."""
        opportunity = LargeCapitalOpportunityFactory()

        result = SearchLargeCapitalOpportunity.db_object_to_dict(opportunity)
        keys = {
            '_document_type',
            'type',
            'status',
            'created_by',
            'uk_region_locations',
            'promoters',
            'required_checks_conducted',
            'required_checks_conducted_by',
            'lead_dit_relationship_manager',
            'other_dit_contacts',
            'asset_classes',
            'opportunity_value',
            'opportunity_value_type',
            'investment_types',
            'construction_risks',
            'estimated_return_rate',
            'time_horizons',
            'investment_projects',
            'sources_of_funding',
            'reasons_for_abandonment',
            'name',
            'current_investment_secured',
            'dit_support_provided',
            'description',
            'id',
            'total_investment_sought',
            'created_on',
            'required_checks_conducted_on',
            'modified_on',
        }
        assert set(result.keys()) == keys

    def test_large_capital_opportunity_dbmodels_to_documents(self, opensearch):
        """Tests conversion of db models to OpenSearch documents."""
        opportunities = LargeCapitalOpportunityFactory.create_batch(2)

        result = SearchLargeCapitalOpportunity.db_objects_to_documents(opportunities)

        assert len(list(result)) == len(opportunities)
