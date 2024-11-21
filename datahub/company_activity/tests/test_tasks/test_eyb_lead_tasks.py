from unittest import mock

import pytest

from datahub.company_activity.models import CompanyActivity
from datahub.company_activity.tasks.sync import (
    relate_company_activity_to_eyb_lead,
    schedule_sync_data_to_company_activity,
)
from datahub.investment_lead.test.factories import EYBLeadFactory


@pytest.mark.django_db
class TestCompanyActivityEYBLeadTasks:
    """
    Tests for the schedule_sync_data_to_company_activity task.
    """

    def test_eyb_leads_are_copied_to_company_activity(self):
        """
        Test that eyb leads are added to the CompanyActivity model.
        """
        eyb_leads = EYBLeadFactory.create_batch(5)

        # Remove the created CompanyActivities added by the eyb lead `save` method
        # to mimic already existing data in staging and prod database.
        CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Check the "existing" eyb leads are added to the company activity model
        schedule_sync_data_to_company_activity(relate_company_activity_to_eyb_lead)
        assert CompanyActivity.objects.count() == len(eyb_leads)

        company_activity = CompanyActivity.objects.get(eyb_lead=eyb_leads[0])
        assert company_activity.date == eyb_leads[0].created_on
        assert company_activity.activity_source == CompanyActivity.ActivitySource.eyb_lead
        assert company_activity.eyb_lead.id == eyb_leads[0].id

    @mock.patch('datahub.company_activity.models.CompanyActivity.objects.bulk_create')
    def test_eyb_leads_are_bulk_created_in_batches(self, mocked_bulk_create, caplog):
        """
        Test that eyb leads are bulk created in batches.
        """
        caplog.set_level('INFO')
        batch_size = 5

        EYBLeadFactory.create_batch(10)

        # Delete any activity created through the investments save method.
        CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Ensure eyb leads are bulk_created
        relate_company_activity_to_eyb_lead(batch_size)
        assert mocked_bulk_create.call_count == 2

        assert (
            f'Creating in batches of: {batch_size} CompanyActivities. 10 remaining.' in caplog.text
        )
        assert (
            f'Creating in batches of: {batch_size} CompanyActivities. 5 remaining.' in caplog.text
        )
        assert 'Finished bulk creating CompanyActivities.' in caplog.text

    def test_eyb_leads_with_a_company_activity_are_not_added_again(self):
        """
        Test that eyb leads which are already part of the `CompanyActivity` model
        are not added again.
        """
        EYBLeadFactory.create_batch(4)

        assert CompanyActivity.objects.count() == 4

        # Check count remains unchanged.
        schedule_sync_data_to_company_activity(relate_company_activity_to_eyb_lead)
        assert CompanyActivity.objects.count() == 4
