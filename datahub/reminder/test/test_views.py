from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin
from datahub.interaction.test.factories import CompaniesInteractionFactory
from datahub.investment.project.proposition.models import PropositionStatus
from datahub.investment.project.proposition.test.factories import PropositionFactory
from datahub.reminder.models import (
    NoRecentExportInteractionReminder,
    NoRecentInvestmentInteractionReminder,
    UpcomingEstimatedLandDateReminder,
)
from datahub.reminder.test.factories import (
    NoRecentExportInteractionReminderFactory,
    NoRecentExportInteractionSubscriptionFactory,
    NoRecentInvestmentInteractionReminderFactory,
    NoRecentInvestmentInteractionSubscriptionFactory,
    UpcomingEstimatedLandDateReminderFactory,
    UpcomingEstimatedLandDateSubscriptionFactory,
)


class TestNoRecentInvestmentInteractionSubscriptionViewset(APITestMixin):
    """
    Tests for the no recent investment interation subscription view.
    """

    url_name = 'api-v4:reminder:no-recent-investment-interaction-subscription'

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse(self.url_name)
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_subscription_not_present(self):
        """Given the current user does not have a subscription, make an empty one"""
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [],
            'email_reminders_enabled': False,
        }

    def test_get_subscription(self):
        """Given an existing subscription, those details should be returned"""
        NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=self.user,
            reminder_days=[10, 20, 40],
            email_reminders_enabled=True,
        )
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [10, 20, 40],
            'email_reminders_enabled': True,
        }

    def test_patch_existing_subscription(self):
        """Patching the subscription will update an existing subscription"""
        NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=self.user,
            reminder_days=[10, 20, 40],
            email_reminders_enabled=True,
        )
        url = reverse(self.url_name)
        data = {'reminder_days': [15, 30], 'email_reminders_enabled': False}
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [15, 30],
            'email_reminders_enabled': False,
        }

    def test_400_patch_existing_subscription_duplicate_days(self):
        """Patching the subscription will update an existing subscription"""
        NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=self.user,
            reminder_days=[10, 20, 40],
            email_reminders_enabled=True,
        )
        url = reverse(self.url_name)
        data = {'reminder_days': [15, 15], 'email_reminders_enabled': False}
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'reminder_days': ['Duplicate reminder days are not allowed [15]'],
        }

    def test_patch_subscription_no_existing(self):
        """Patching the subscription will create one if it didn't exist already"""
        url = reverse(self.url_name)
        data = {'reminder_days': [15]}
        response = self.api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [15],
            'email_reminders_enabled': False,
        }

    def test_400_patch_subscription_no_existing_duplicate_days(self):
        """Patching the subscription will create one if it didn't exist already"""
        url = reverse(self.url_name)
        data = {'reminder_days': [10, 10, 15]}
        response = self.api_client.patch(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'reminder_days': ['Duplicate reminder days are not allowed [10]'],
        }


class TestUpcomingEstimatedLandDateSubscriptionViewset(APITestMixin):
    """
    Tests for the upcoming estimated land date subscription view.
    """

    url_name = 'api-v4:reminder:estimated-land-date-subscription'

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse(self.url_name)
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_subscription_not_present(self):
        """Given the current user does not have a subscription, make an empty one"""
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [],
            'email_reminders_enabled': False,
        }

    def test_get_subscription(self):
        """Given an existing subscription, those details should be returned"""
        UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=self.user,
            reminder_days=[10, 20, 40],
            email_reminders_enabled=True,
        )
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [10, 20, 40],
            'email_reminders_enabled': True,
        }

    def test_patch_existing_subscription(self):
        """Patching the subscription will update an existing subscription"""
        UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=self.user,
            reminder_days=[10, 20, 40],
            email_reminders_enabled=True,
        )
        url = reverse(self.url_name)
        data = {'reminder_days': [15, 30], 'email_reminders_enabled': False}
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [15, 30],
            'email_reminders_enabled': False,
        }

    def test_patch_subscription_no_existing(self):
        """Patching the subscription will create one if it didn't exist already"""
        url = reverse(self.url_name)
        data = {'reminder_days': [15]}
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [15],
            'email_reminders_enabled': False,
        }


class TestNoRecentExportInteractionSubscriptionViewset(APITestMixin):
    """
    Tests for the no recent export interaction subscription view.
    """

    url_name = 'api-v4:reminder:no-recent-export-interaction-subscription'

    def test_get_subscription_not_present(self):
        """Given the current user does not have a subscription, make an empty one"""
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [],
            'email_reminders_enabled': False,
        }

    def test_get_subscription(self):
        """Given an existing subscription, those details should be returned"""
        NoRecentExportInteractionSubscriptionFactory(
            adviser=self.user,
            reminder_days=[10, 20, 40],
            email_reminders_enabled=True,
        )
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [10, 20, 40],
            'email_reminders_enabled': True,
        }

    def test_patch_existing_subscription(self):
        """Patching the subscription will update an existing subscription"""
        NoRecentExportInteractionSubscriptionFactory(
            adviser=self.user,
            reminder_days=[10, 20, 40],
            email_reminders_enabled=True,
        )
        url = reverse(self.url_name)
        data = {'reminder_days': [15, 30], 'email_reminders_enabled': False}
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [15, 30],
            'email_reminders_enabled': False,
        }

    def test_400_patch_existing_subscription_duplicate_days(self):
        """Patching the subscription will update an existing subscription"""
        NoRecentExportInteractionSubscriptionFactory(
            adviser=self.user,
            reminder_days=[10, 20, 40],
            email_reminders_enabled=True,
        )
        url = reverse(self.url_name)
        data = {'reminder_days': [15, 15], 'email_reminders_enabled': False}
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'reminder_days': ['Duplicate reminder days are not allowed [15]'],
        }

    def test_patch_subscription_no_existing(self):
        """Patching the subscription will create one if it didn't exist already"""
        url = reverse(self.url_name)
        data = {'reminder_days': [15]}
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [15],
            'email_reminders_enabled': False,
        }


class TestGetReminderSubscriptionSummaryView(APITestMixin):
    """
    Tests for the reminder subscription summary view.
    """

    url_name = 'api-v4:reminder:subscription-summary'

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse(self.url_name)
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_summary_of_reminders(self):
        """Should return a summary of reminders"""
        reminder_days = [10, 20, 40]
        email_reminders_enabled = True

        NoRecentExportInteractionSubscriptionFactory(
            adviser=self.user,
            reminder_days=reminder_days,
            email_reminders_enabled=email_reminders_enabled,
        )
        NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=self.user,
            reminder_days=reminder_days,
            email_reminders_enabled=email_reminders_enabled,
        )
        UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=self.user,
            reminder_days=reminder_days,
            email_reminders_enabled=email_reminders_enabled,
        )

        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            'estimated_land_date': {
                'email_reminders_enabled': True, 'reminder_days': [10, 20, 40],
            },
            'no_recent_investment_interaction': {
                'email_reminders_enabled': True, 'reminder_days': [10, 20, 40],
            },
            'no_recent_export_interaction': {
                'email_reminders_enabled': True, 'reminder_days': [10, 20, 40],
            },
        }

    def test_no_subscriptions(self):
        """Should return base summary cases."""
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            'estimated_land_date': {
                'email_reminders_enabled': False, 'reminder_days': [],
            },
            'no_recent_investment_interaction': {
                'email_reminders_enabled': False, 'reminder_days': [],
            },
            'no_recent_export_interaction': {
                'email_reminders_enabled': False, 'reminder_days': [],
            },
        }


@freeze_time('2022-11-07T17:00:00.000000Z')
class TestNoRecentExportInteractionReminderViewset(APITestMixin):
    """
    Tests for the no recent export interaction reminder view.
    """

    url_name = 'api-v4:reminder:no-recent-export-interaction-reminder'
    detail_url_name = 'api-v4:reminder:no-recent-export-interaction-reminder-detail'

    def create_reminders(self):
        """Creates some mock reminders"""
        with freeze_time('2022-11-07T17:00:00.000000Z'):
            reminder_1 = NoRecentExportInteractionReminderFactory(
                adviser=self.user,
            )
        with freeze_time('2022-11-07T18:00:00.000000Z'):
            reminder_2 = NoRecentExportInteractionReminderFactory(
                adviser=self.user,
            )
        return [reminder_1, reminder_2]

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse(self.url_name)
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_reminders(self):
        """Given some reminders, these should be returned"""
        reminder_count = 3
        export_company = CompanyFactory()
        export_interaction = CompaniesInteractionFactory()
        reminders = NoRecentExportInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
            company=export_company,
            interaction=export_interaction,
        )
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == reminder_count
        assert 'next' in data
        assert 'previous' in data
        results = data.get('results', [])
        assert len(results) == 2
        reminders = sorted(reminders, key=lambda x: x.pk)

        assert results[0] == {
            'id': str(reminders[0].id),
            'created_on': '2022-11-07T17:00:00Z',
            'event': reminders[0].event,
            'company': {
                'id': str(export_company.id),
                'name': export_company.name,
            },
            'interaction': {
                'created_by': {
                    'name': export_interaction.created_by.name,
                    'first_name': export_interaction.created_by.first_name,
                    'last_name': export_interaction.created_by.last_name,
                    'id': str(export_interaction.created_by.id),
                    'dit_team': {
                        'id': str(export_interaction.created_by.dit_team.id),
                        'name': export_interaction.created_by.dit_team.name,
                    },
                },
                'kind': str(export_interaction.kind),
                'subject': export_interaction.subject,
            },
        }

    def test_get_reminders_only_includes_current(self):
        """Only the reminders belonging to the current user should be returned"""
        reminder_count = 3
        NoRecentExportInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        NoRecentExportInteractionReminderFactory.create_batch(2)
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == reminder_count

    def test_default_sort_by(self):
        """Defaut sort should be in reverse date order"""
        reminder_1, reminder_2 = self.create_reminders()
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == 2
        results = data.get('results', [])
        assert results[0]['id'] == str(reminder_2.id)
        assert results[1]['id'] == str(reminder_1.id)

    def test_sort_by_created(self):
        """Should sort in date order"""
        reminder_1, reminder_2 = self.create_reminders()
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2&sortby=created_on')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == 2
        results = data.get('results', [])
        assert results[0]['id'] == str(reminder_1.id)
        assert results[1]['id'] == str(reminder_2.id)

    def test_sort_by_created_descending(self):
        """Should sort in reverse date order"""
        reminder_1, reminder_2 = self.create_reminders()
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2&sortby=-created_on')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == 2
        results = data.get('results', [])
        assert results[0]['id'] == str(reminder_2.id)
        assert results[1]['id'] == str(reminder_1.id)

    def test_delete(self):
        """Deleting should remove the model instance"""
        reminder_count = 3
        reminder = NoRecentExportInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )[0]
        url = reverse(self.detail_url_name, kwargs={'pk': str(reminder.id)})
        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert NoRecentExportInteractionReminder.objects.filter(
            adviser=self.user,
        ).count() == reminder_count - 1

    def test_get_reminders_no_team(self):
        """Should be return reminders of interactions created by users with no DIT team listed"""
        interaction_adviser = AdviserFactory(dit_team=None)
        export_interaction = CompaniesInteractionFactory(created_by=interaction_adviser)

        NoRecentExportInteractionReminderFactory.create(
            adviser=self.user, interaction=export_interaction
        )

        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        returned_reminder = data['results'][0]
        assert returned_reminder['interaction']['created_by']['dit_team'] is None


@freeze_time('2022-05-05T17:00:00.000000Z')
class TestNoRecentInvestmentInteractionReminderViewset(APITestMixin):
    """
    Tests for the no recent investment interaction reminder view.
    """

    url_name = 'api-v4:reminder:no-recent-investment-interaction-reminder'
    detail_url_name = 'api-v4:reminder:no-recent-investment-interaction-reminder-detail'

    def create_reminders(self):
        """Creates some mock reminders"""
        with freeze_time('2022-05-05T18:00:00.000000Z'):
            reminder_1 = NoRecentInvestmentInteractionReminderFactory(
                adviser=self.user,
            )
        with freeze_time('2022-05-05T19:00:00.000000Z'):
            reminder_2 = NoRecentInvestmentInteractionReminderFactory(
                adviser=self.user,
            )
        return [reminder_1, reminder_2]

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse(self.url_name)
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_reminders(self):
        """Given some reminders, these should be returned"""
        reminder_count = 3
        reminders = NoRecentInvestmentInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == reminder_count
        assert 'next' in data
        assert 'previous' in data
        results = data.get('results', [])
        assert len(results) == 2
        reminders = sorted(reminders, key=lambda x: x.pk)
        assert results[0] == {
            'id': str(reminders[0].id),
            'created_on': '2022-05-05T17:00:00Z',
            'event': reminders[0].event,
            'project': {
                'id': str(reminders[0].project.id),
                'name': reminders[0].project.name,
                'project_code': reminders[0].project.project_code,
            },
        }

    def test_get_reminders_only_includes_current(self):
        """Only the reminders belonging to the current user should be returned"""
        reminder_count = 3
        NoRecentInvestmentInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        NoRecentInvestmentInteractionReminderFactory.create_batch(2)
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == reminder_count

    def test_default_sort_by(self):
        """Default sort should be in reverse date order"""
        reminder_1, reminder_2 = self.create_reminders()
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == 2
        results = data.get('results', [])
        assert results[0]['id'] == str(reminder_2.id)
        assert results[1]['id'] == str(reminder_1.id)

    def test_sort_by_created(self):
        """Should sort in date order"""
        reminder_1, reminder_2 = self.create_reminders()
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2&sortby=created_on')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == 2
        results = data.get('results', [])
        assert results[0]['id'] == str(reminder_1.id)
        assert results[1]['id'] == str(reminder_2.id)

    def test_sort_by_created_descending(self):
        """Should sort in reverse date order"""
        reminder_1, reminder_2 = self.create_reminders()
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2&sortby=-created_on')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == 2
        results = data.get('results', [])
        assert results[0]['id'] == str(reminder_2.id)
        assert results[1]['id'] == str(reminder_1.id)

    def test_delete(self):
        """Deleting should remove the model instance"""
        reminder_count = 3
        reminder = NoRecentInvestmentInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )[0]
        url = reverse(self.detail_url_name, kwargs={'pk': str(reminder.id)})
        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert NoRecentInvestmentInteractionReminder.objects.filter(
            adviser=self.user,
        ).count() == reminder_count - 1


@freeze_time('2022-05-05T17:00:00.000000Z')
class TestUpcomingEstimatedLandDateReminderViewset(APITestMixin):
    """
    Tests for the upcoming estimated land date reminder view.
    """

    url_name = 'api-v4:reminder:estimated-land-date-reminder'
    detail_url_name = 'api-v4:reminder:estimated-land-date-reminder-detail'

    def create_reminders(self):
        """Creates some mock reminders"""
        with freeze_time('2022-05-05T18:00:00.000000Z'):
            reminder_1 = UpcomingEstimatedLandDateReminderFactory(
                adviser=self.user,
            )
        with freeze_time('2022-05-05T19:00:00.000000Z'):
            reminder_2 = UpcomingEstimatedLandDateReminderFactory(
                adviser=self.user,
            )
        return [reminder_1, reminder_2]

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse(self.url_name)
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_reminders(self):
        """Given some reminders, these should be returned"""
        reminder_count = 3
        reminders = UpcomingEstimatedLandDateReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == reminder_count
        assert 'next' in data
        assert 'previous' in data
        results = data.get('results', [])
        assert len(results) == 2
        reminders = sorted(reminders, key=lambda x: x.pk)
        assert results[0] == {
            'id': str(reminders[0].id),
            'created_on': '2022-05-05T17:00:00Z',
            'event': reminders[0].event,
            'project': {
                'id': str(reminders[0].project.id),
                'name': reminders[0].project.name,
                'project_code': reminders[0].project.project_code,
            },
        }

    def test_get_reminders_only_includes_current(self):
        """Only the reminders belonging to the current user should be returned"""
        reminder_count = 3
        UpcomingEstimatedLandDateReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        UpcomingEstimatedLandDateReminderFactory.create_batch(2)
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == reminder_count

    def test_default_sort_by(self):
        """Default sort should be in reverse date order"""
        reminder_1, reminder_2 = self.create_reminders()
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == 2
        results = data.get('results', [])
        assert results[0]['id'] == str(reminder_2.id)
        assert results[1]['id'] == str(reminder_1.id)

    def test_sort_by_created(self):
        """Should sort in date order"""
        reminder_1, reminder_2 = self.create_reminders()
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2&sortby=created_on')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == 2
        results = data.get('results', [])
        assert results[0]['id'] == str(reminder_1.id)
        assert results[1]['id'] == str(reminder_2.id)

    def test_sort_by_created_descending(self):
        """Should sort in reverse date order"""
        reminder_1, reminder_2 = self.create_reminders()
        url = reverse(self.url_name)
        response = self.api_client.get(f'{url}?offset=0&limit=2&sortby=-created_on')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == 2
        results = data.get('results', [])
        assert results[0]['id'] == str(reminder_2.id)
        assert results[1]['id'] == str(reminder_1.id)

    def test_delete(self):
        """Deleting should remove the model instance"""
        reminder_count = 3
        reminder = UpcomingEstimatedLandDateReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )[0]
        url = reverse(self.detail_url_name, kwargs={'pk': str(reminder.id)})
        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert UpcomingEstimatedLandDateReminder.objects.filter(
            adviser=self.user,
        ).count() == reminder_count - 1


class TestGetReminderSummaryView(APITestMixin):
    """
    Tests for the reminder summary view.
    """

    url_name = 'api-v4:reminder:summary'

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse(self.url_name)
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_summary_of_reminders(self):
        """Should return a summary of reminders."""
        reminder_count = 3
        UpcomingEstimatedLandDateReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        UpcomingEstimatedLandDateReminderFactory.create_batch(2)
        NoRecentInvestmentInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        NoRecentInvestmentInteractionReminderFactory.create_batch(2)
        PropositionFactory.create_batch(
            reminder_count,
            adviser=self.user,
            status=PropositionStatus.ONGOING,
        )
        PropositionFactory(
            adviser=self.user,
            status=PropositionStatus.ABANDONED,
        )
        PropositionFactory.create_batch(2)
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            'estimated_land_date': reminder_count,
            'no_recent_investment_interaction': reminder_count,
            'outstanding_propositions': reminder_count,
        }

    def test_get_zeroes_if_no_reminders(self):
        """Should return zeroes if user does not have any reminders."""
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            'estimated_land_date': 0,
            'no_recent_investment_interaction': 0,
            'outstanding_propositions': 0,
        }
