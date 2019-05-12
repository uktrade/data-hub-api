import pytest
from django.db.utils import IntegrityError

from datahub.investment.investor_profile.test.factories import LargeCapitalInvestorProfileFactory


pytestmark = pytest.mark.django_db


class TestLargeCapitalInvestorProfileModel:
    """Tests for the LargeCapitalInvestorProfile model."""

    def test_raises_error_when_required_fields_not_provided(self):
        """Tests an integrity error is raised when any of the required fields are missing."""
        with pytest.raises(IntegrityError):
            LargeCapitalInvestorProfileFactory(investor_company=None)
