from unittest import mock

import pytest

from datahub.company_activity.models import CompanyActivity
from datahub.company_activity.tasks.sync import (
    relate_company_activity_to_referrals,
    schedule_sync_data_to_company_activity,
)
from datahub.company_referral.test.factories import CompanyReferralFactory


@pytest.mark.django_db
class TestCompanyActivityReferralTasks:
    """Tests for the schedule_sync_referrals_to_company_activity task."""

    def test_referral_are_copied_to_company_activity(self):
        """Test that referrals are added to the CompanyActivity model."""
        referral = CompanyReferralFactory()
        CompanyReferralFactory()
        CompanyReferralFactory()
        CompanyReferralFactory()

        # Remove the created CompanyActivities added by the CompanyReferral `save` method
        # to mimick already existing data in staging and prod database.
        CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Check the "existing" referrals are addded to the company activity model
        schedule_sync_data_to_company_activity(relate_company_activity_to_referrals)
        assert CompanyActivity.objects.count() == 4

        company_activity = CompanyActivity.objects.get(referral_id=referral.id)
        assert company_activity.date == referral.created_on
        assert company_activity.activity_source == CompanyActivity.ActivitySource.referral
        assert company_activity.company_id == referral.company_id

    def test_referral_with_a_company_activity_are_not_added_again(self):
        """Test that referrals which are already part of the `CompanyActivity` model
        are not added again.
        """
        CompanyReferralFactory()
        CompanyReferralFactory()
        CompanyReferralFactory()
        CompanyReferralFactory()

        assert CompanyActivity.objects.count() == 4

        # Check count remains unchanged.
        schedule_sync_data_to_company_activity(relate_company_activity_to_referrals)
        assert CompanyActivity.objects.count() == 4

    @mock.patch('datahub.company_activity.models.CompanyActivity.objects.bulk_create')
    def test_referrals_are_bulk_created_in_batches(self, mocked_bulk_create, caplog):
        """Test that referrals are bulk created in batches."""
        caplog.set_level('INFO')
        batch_size = 5

        CompanyReferralFactory.create_batch(10)

        # Delete any activity created through the referrals save method.
        CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Ensure referrals are bulk_created
        relate_company_activity_to_referrals(batch_size)
        assert mocked_bulk_create.call_count == 2

        assert (
            f'Creating in batches of: {batch_size} CompanyActivities. 10 remaining.' in caplog.text
        )
        assert (
            f'Creating in batches of: {batch_size} CompanyActivities. 5 remaining.' in caplog.text
        )
        assert 'Finished bulk creating CompanyActivities.' in caplog.text
