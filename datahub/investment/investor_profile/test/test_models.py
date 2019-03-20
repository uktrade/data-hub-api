import pytest
from django.db.utils import IntegrityError

from datahub.company.test.factories import CompanyFactory
from datahub.investment.investor_profile.test.factories import LargeInvestorProfileFactory


pytestmark = pytest.mark.django_db


class TestInvestorProfileModel:
    """Tests for the InvestorProfile model."""

    def test_raises_error_when_profile_of_same_type_already_exists(self):
        """
        Tests an integrity error is raised when a company already has a profile of the same type.
        """
        investor_company = CompanyFactory()
        LargeInvestorProfileFactory(
            investor_company=investor_company,
        )
        with pytest.raises(IntegrityError):
            LargeInvestorProfileFactory(
                investor_company=investor_company,
            )

    @pytest.mark.parametrize(
        'parameters',
        (
            {'profile_type_id': None},
            {'investor_company': None},
        ),
    )
    def test_raises_error_when_required_fields_not_provided(self, parameters):
        """Tests an integrity error is raised when any of the required fields are missing."""
        with pytest.raises(IntegrityError):
            LargeInvestorProfileFactory(**parameters)
