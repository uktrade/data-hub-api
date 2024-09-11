import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.models import CompanyActivity
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

    def test_save(self):
        """
        Test save also saves to the `CompanyActivity` model.
        Test save does not save to the `CompanyActivity` model if it already exists.
        """
        assert CompanyActivity.objects.all().count() == 0
        referral = CompanyReferralFactory()
        assert CompanyActivity.objects.all().count() == 1

        company_activity = CompanyActivity.objects.get(referral_id=referral.id)
        assert company_activity.company_id == referral.company_id
        assert company_activity.date == referral.created_on
        assert company_activity.activity_source == CompanyActivity.ActivitySource.referral

        # Update and save the referral and ensure if doesn't create another
        # `CompanyActivity` and only updates it
        new_company = CompanyFactory()
        referral.company_id = new_company.id
        referral.save()

        assert CompanyActivity.objects.all().count() == 1
        company_activity.refresh_from_db()
        assert company_activity.company_id == new_company.id
