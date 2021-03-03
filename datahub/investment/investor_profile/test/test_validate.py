import pytest

from datahub.investment.investor_profile.models import LargeCapitalInvestorProfile
from datahub.investment.investor_profile.test.factories import LargeCapitalInvestorProfileFactory
from datahub.investment.investor_profile.validate import get_incomplete_fields

pytestmark = pytest.mark.django_db


def test_incomplete_fields():
    """Tests incomplete fields on an investor profile are returned."""
    instance = LargeCapitalInvestorProfileFactory.build()
    result = get_incomplete_fields(
        instance,
        ['investor_company', 'investor_description'],
        LargeCapitalInvestorProfile,
    )
    assert result == ['investor_description']
