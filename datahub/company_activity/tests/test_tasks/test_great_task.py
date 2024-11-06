from unittest import mock

import pytest

from datahub.company_activity.models import CompanyActivity
from datahub.company_activity.tasks.sync import (
    relate_company_activity_to_great,
    schedule_sync_data_to_company_activity,
)
from datahub.company_activity.tests.factories import CompanyActivityGreatExportEnquiryFactory


@pytest.mark.django_db
class TestCompanyActivityGreatTasks:
    """
    Tests for the schedule_sync_investments_to_company_activity task.
    """

    def test_great_export_enquiry_are_copied_to_company_activity(self):
        """
        Test that investments are added to the CompanyActivity model.
        """
        great = CompanyActivityGreatExportEnquiryFactory()
        CompanyActivityGreatExportEnquiryFactory()
        CompanyActivityGreatExportEnquiryFactory()
        CompanyActivityGreatExportEnquiryFactory()

        # Remove the created CompanyActivities added by the Great model `save` method
        # to mimic already existing data in staging and prod database.
        CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Check the "existing" great are added to the company activity model
        schedule_sync_data_to_company_activity(relate_company_activity_to_great)
        assert CompanyActivity.objects.count() == 4

        company_activity = CompanyActivity.objects.get(great_id=great.id)
        assert company_activity.date == great.created_on
        assert company_activity.activity_source == CompanyActivity.ActivitySource.great
        assert company_activity.company_id == great.company.id

    @mock.patch('datahub.company_activity.models.CompanyActivity.objects.bulk_create')
    def test_investment_are_bulk_created_in_batches(self, mocked_bulk_create, caplog):
        """
        Test that investment projects are bulk created in batches.
        """
        caplog.set_level('INFO')
        batch_size = 5

        CompanyActivityGreatExportEnquiryFactory.create_batch(10)

        # Delete any activity created through the investments save method.
        CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Ensure investments are bulk_created
        relate_company_activity_to_great(batch_size)
        assert mocked_bulk_create.call_count == 2

        assert (
            f'Creating in batches of: {batch_size} CompanyActivities. 10 remaining.' in caplog.text
        )
        assert (
            f'Creating in batches of: {batch_size} CompanyActivities. 5 remaining.' in caplog.text
        )
        assert 'Finished bulk creating CompanyActivities.' in caplog.text

    def test_investment_with_a_company_activity_are_not_added_again(self):
        """
        Test that investment projects which are already part of the `CompanyActivity` model
        are not added again.
        """
        CompanyActivityGreatExportEnquiryFactory()
        CompanyActivityGreatExportEnquiryFactory()
        CompanyActivityGreatExportEnquiryFactory()
        CompanyActivityGreatExportEnquiryFactory()

        assert CompanyActivity.objects.count() == 4

        # Check count remains unchanged.
        schedule_sync_data_to_company_activity(relate_company_activity_to_great)
        assert CompanyActivity.objects.count() == 4
