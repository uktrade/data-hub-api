import pytest

from datahub.company_activity.tasks import schedule_sync_interactions_to_company_activity
from datahub.company_activity.models import CompanyActivity
from datahub.interaction.test.factories import CompanyInteractionFactory


@pytest.mark.django_db
class TestCompanyActivityInteractionTasks:
    """
    Tests for the schedule_sync_interactions_to_company_activity task.
    """

    def test_interactions_are_copied_to_company_activity(self):
        """
        Test that interactions are added to the CompanyActivity model.
        """
        interaction = CompanyInteractionFactory()
        CompanyInteractionFactory()
        CompanyInteractionFactory()
        CompanyInteractionFactory()

        # Remove the created CompanyActivities added by the Interactions `save` method
        # to mimick already existing data in staging and prod database.
        assert CompanyActivity.objects.all().delete()
        assert CompanyActivity.objects.count() == 0

        # Check the "existing" interactions are addded to the company activity model
        schedule_sync_interactions_to_company_activity()
        assert CompanyActivity.objects.count() == 4

        company_activity = CompanyActivity.objects.get(interaction_id=interaction.id)
        assert company_activity.date == interaction.date
        assert company_activity.activity_source == CompanyActivity.ActivitySource.interaction
        assert company_activity.company_id == interaction.company_id

    def test_interactions_with_a_company_activity_are_not_added_again(self):
        """
        Test that interactions which are already part of the `CompanyActivity` model
        are not added again.
        """
        CompanyInteractionFactory()
        CompanyInteractionFactory()
        CompanyInteractionFactory()
        CompanyInteractionFactory()

        assert CompanyActivity.objects.count() == 4

        # Check count remains unchanged.
        schedule_sync_interactions_to_company_activity()
        assert CompanyActivity.objects.count() == 4
