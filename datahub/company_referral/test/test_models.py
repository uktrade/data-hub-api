import pytest

from datahub.company_referral.test.factories import CompanyReferralFactory


@pytest.mark.django_db
class TestCompanyReferral:
    """Tests for the CompanyReferral model."""

    def test_str(self):
        """Test __str__()."""
        referral = CompanyReferralFactory.build(
            company__name='Mars Ltd',
            subject='Wants to export to the Far East',
        )
        assert str(referral) == 'Mars Ltd – Wants to export to the Far East'
