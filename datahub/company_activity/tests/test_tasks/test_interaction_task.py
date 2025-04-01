from unittest import mock

import pytest

from datahub.company_activity.models import CompanyActivity
from datahub.company_activity.tasks.sync import (
    relate_company_activity_to_interactions,
    schedule_sync_data_to_company_activity,
)
from datahub.interaction.test.factories import CompanyInteractionFactory


@pytest.mark.django_db
class TestCompanyActivityInteractionTasks:
    """Tests for the schedule_sync_interactions_to_company_activity task."""

    def test_interactions_are_copied_to_company_activity(self):
        """Test that interactions are added to the CompanyActivity model."""
        interaction = CompanyInteractionFactory()
        CompanyInteractionFactory()
        CompanyInteractionFactory()
        CompanyInteractionFactory()

        # Remove the created CompanyActivities added by the Interactions `save` method
        # to mimick already existing data in staging and prod database.
        CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Check the "existing" interactions are addded to the company activity model
        schedule_sync_data_to_company_activity(relate_company_activity_to_interactions)
        assert CompanyActivity.objects.count() == 4

        company_activity = CompanyActivity.objects.get(interaction_id=interaction.id)
        assert company_activity.date == interaction.date
        assert company_activity.activity_source == CompanyActivity.ActivitySource.interaction
        assert company_activity.company_id == interaction.company_id

    def test_interactions_with_a_company_activity_are_not_added_again(self):
        """Test that interactions which are already part of the `CompanyActivity` model
        are not added again.
        """
        CompanyInteractionFactory()
        CompanyInteractionFactory()
        CompanyInteractionFactory()
        CompanyInteractionFactory()

        assert CompanyActivity.objects.count() == 4

        # Check count remains unchanged.
        schedule_sync_data_to_company_activity(relate_company_activity_to_interactions)
        assert CompanyActivity.objects.count() == 4

    def test_interactions_without_a_company_activity_are_not_added(self):
        """Test that interactions which have no company are not added."""
        CompanyInteractionFactory(company=None)

        # Delete any activity created through the interactions save method.
        CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Schedule the sync and ensure interaction with no company is not added.
        schedule_sync_data_to_company_activity(relate_company_activity_to_interactions)
        assert CompanyActivity.objects.count() == 0

    @mock.patch('datahub.company_activity.models.CompanyActivity.objects.bulk_create')
    def test_interactions_are_bulk_created_in_batches(self, mocked_bulk_create, caplog):
        """Test that interactions are bulk created in batches."""
        caplog.set_level('INFO')
        batch_size = 5

        CompanyInteractionFactory.create_batch(10)

        # Delete any activity created through the interactions save method.
        CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Ensure interaction are bulk_created
        relate_company_activity_to_interactions(batch_size)
        assert mocked_bulk_create.call_count == 2

        assert (
            f'Creating in batches of: {batch_size} CompanyActivities. 10 remaining.' in caplog.text
        )
        assert (
            f'Creating in batches of: {batch_size} CompanyActivities. 5 remaining.' in caplog.text
        )
        assert 'Finished bulk creating CompanyActivities.' in caplog.text
