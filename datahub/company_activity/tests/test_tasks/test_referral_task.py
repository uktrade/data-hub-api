import pytest

from datahub.company_activity.models import CompanyActivity
from datahub.company_activity.tasks import schedule_sync_referrals_to_company_activity
from datahub.company_referral.test.factories import CompanyReferralFactory


@pytest.mark.django_db
class TestCompanyActivityReferralTasks:
    """
    Tests for the schedule_sync_referrals_to_company_activity task.
    """

    def test_referral_are_copied_to_company_activity(self):
        """
        Test that referrals are added to the CompanyActivity model.
        """
        referral = CompanyReferralFactory()
        CompanyReferralFactory()
        CompanyReferralFactory()
        CompanyReferralFactory()

        # Remove the created CompanyActivities added by the CompanyReferral `save` method
        # to mimick already existing data in staging and prod database.
        assert CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Check the "existing" referrals are addded to the company activity model
        schedule_sync_referrals_to_company_activity()
        assert CompanyActivity.objects.count() == 4

        company_activity = CompanyActivity.objects.get(referral_id=referral.id)
        assert company_activity.date == referral.created_on
        assert company_activity.activity_source == CompanyActivity.ActivitySource.referral
        assert company_activity.company_id == referral.company_id

    def test_referral_with_a_company_activity_are_not_added_again(self):
        """
        Test that referrals which are already part of the `CompanyActivity` model
        are not added again.
        """
        CompanyReferralFactory()
        CompanyReferralFactory()
        CompanyReferralFactory()
        CompanyReferralFactory()

        assert CompanyActivity.objects.count() == 4

        # Check count remains unchanged.
        schedule_sync_referrals_to_company_activity()
        assert CompanyActivity.objects.count() == 4
