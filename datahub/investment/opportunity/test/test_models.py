import pytest
from django.db.utils import IntegrityError

from datahub.investment.opportunity.test.factories import (
    CompleteLargeCapitalOpportunityFactory,
    LargeCapitalOpportunityFactory,
)


pytestmark = pytest.mark.django_db


class TestLargeCapitalOpportunityModel:
    """Tests for the LargeCapitalOpportunity model."""

    def test_can_create_large_capital_opportunity(self):
        """Tests that a large capital opportunity can be created."""
        try:
            CompleteLargeCapitalOpportunityFactory()
        except Exception:
            pytest.fail('Cannot create large capital opportunity.')

    def test_raises_error_when_required_fields_not_provided(self):
        """Tests an integrity error is raised when any of the required fields are missing."""
        with pytest.raises(IntegrityError):
            LargeCapitalOpportunityFactory(
                lead_dit_relationship_manager=None,
                dit_support_provided=None,
            )
