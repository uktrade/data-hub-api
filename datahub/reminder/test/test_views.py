import pytest

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.feature_flag.test.factories import UserFeatureFlagGroupFactory
from datahub.interaction.test.factories import CompaniesInteractionFactory
from datahub.investment.project.proposition.models import PropositionStatus
from datahub.investment.project.proposition.test.factories import PropositionFactory
from datahub.reminder import (
    EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME,
)
from datahub.reminder.models import (
    NewExportInteractionReminder,
    NoRecentExportInteractionReminder,
    NoRecentInvestmentInteractionReminder,
    UpcomingEstimatedLandDateReminder,
    UpcomingTaskReminderSubscription,
)
from datahub.reminder.test.factories import (
    NewExportInteractionReminderFactory,
    NewExportInteractionSubscriptionFactory,
    NoRecentExportInteractionReminderFactory,
    NoRecentExportInteractionSubscriptionFactory,
    NoRecentInvestmentInteractionReminderFactory,
    NoRecentInvestmentInteractionSubscriptionFactory,
    UpcomingEstimatedLandDateReminderFactory,
    UpcomingEstimatedLandDateSubscriptionFactory,
    UpcomingTaskReminderSubscriptionFactory,
)


@pytest.fixture()
def investment_notifications_user_feature_group():
    """
    Creates the investment notifications user feature group.
    """
    yield UserFeatureFlagGroupFactory(
        code=INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME,
        is_active=True,
    )


@pytest.fixture()
def export_notifications_user_feature_group():
    """
    Creates the export notifications user feature group.
    """
    yield UserFeatureFlagGroupFactory(
        code=EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
        is_active=True,
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


class TestNewExportInteractionSubscriptionViewset(APITestMixin):
    """
    Tests for the no recent export interaction subscription view.
    """

    url_name = 'api-v4:reminder:new-export-interaction-subscription'

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
        NewExportInteractionSubscriptionFactory(
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
        NewExportInteractionSubscriptionFactory(
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
        NewExportInteractionSubscriptionFactory(
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

        NewExportInteractionSubscriptionFactory(
            adviser=self.user,
            reminder_days=reminder_days,
            email_reminders_enabled=email_reminders_enabled,
        )
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
        UpcomingTaskReminderSubscriptionFactory(
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
                'email_reminders_enabled': True,
                'reminder_days': [10, 20, 40],
            },
            'new_export_interaction': {
                'email_reminders_enabled': True,
                'reminder_days': [10, 20, 40],
            },
            'no_recent_investment_interaction': {
                'email_reminders_enabled': True,
                'reminder_days': [10, 20, 40],
            },
            'no_recent_export_interaction': {
                'email_reminders_enabled': True,
                'reminder_days': [10, 20, 40],
            },
            'no_recent_export_interaction': {
                'email_reminders_enabled': True,
                'reminder_days': [10, 20, 40],
            },
            'upcoming_task_reminder': {
                'email_reminders_enabled': True,
                'reminder_days': [10, 20, 40],
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
                'email_reminders_enabled': False,
                'reminder_days': [],
            },
            'new_export_interaction': {
                'email_reminders_enabled': False,
                'reminder_days': [],
            },
            'no_recent_investment_interaction': {
                'email_reminders_enabled': False,
                'reminder_days': [],
            },
            'no_recent_export_interaction': {
                'email_reminders_enabled': False,
                'reminder_days': [],
            },
            'upcoming_task_reminder': {
                'email_reminders_enabled': False,
                'reminder_days': [],
            },
        }


class ReminderTestMixin:
    """
    Common tests for the reminder views.
    """

    @property
    def get_response(self):
        url = reverse(self.url_name)
        return self.api_client.get(f'{url}?offset=0&limit=2')

    def create_reminders(self):
        """Creates some mock reminders"""
        with freeze_time('2022-11-07T17:00:00.000000Z'):
            reminder_1 = self.factory(
                adviser=self.user,
            )
        with freeze_time('2022-11-07T18:00:00.000000Z'):
            reminder_2 = self.factory(
                adviser=self.user,
            )
        return [reminder_1, reminder_2]

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse(self.url_name)
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_reminders_only_includes_current(self):
        """Only the reminders belonging to the current user should be returned"""
        reminder_count = 3
        self.factory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        self.factory.create_batch(2)
        response = self.get_response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get('count') == reminder_count

    def test_default_sort_by(self):
        """Default sort should be in reverse date order"""
        reminder_1, reminder_2 = self.create_reminders()
        response = self.get_response
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
        reminder = self.factory.create_batch(
            reminder_count,
            adviser=self.user,
        )[0]
        url = reverse(self.detail_url_name, kwargs={'pk': str(reminder.id)})
        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert (
            self.tested_model.objects.filter(
                adviser=self.user,
            ).count()
            == reminder_count - 1
        )


@freeze_time('2022-12-15T17:00:00.000000Z')
class TestNewExportInteractionReminderViewset(APITestMixin, ReminderTestMixin):
    """
    Tests for the new export interaction reminder view.
    """

    url_name = 'api-v4:reminder:new-export-interaction-reminder'
    detail_url_name = 'api-v4:reminder:new-export-interaction-reminder-detail'
    factory = NewExportInteractionReminderFactory
    tested_model = NewExportInteractionReminder

    def test_get_reminders(self):
        """Given some reminders, these should be returned"""
        reminder_count = 3
        export_company = CompanyFactory()
        export_interaction = CompaniesInteractionFactory()
        reminders = NewExportInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
            company=export_company,
            interaction=export_interaction,
        )
        url = reverse(self.url_name)
        response = self.get_response
        assert response.status_code == status.HTTP_200_OK

        sorted_reminders = sorted(reminders, key=lambda x: x.pk)
        data = response.json()
        assert data == {
            'count': reminder_count,
            'next': f'http://testserver{url}?limit=2&offset=2',
            'previous': None,
            'results': [
                {
                    'id': str(sorted_reminders[0].id),
                    'created_on': '2022-12-15T17:00:00Z',
                    'event': sorted_reminders[0].event,
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
                        'date': format_date_or_datetime(export_interaction.date),
                        'kind': str(export_interaction.kind),
                        'subject': export_interaction.subject,
                    },
                    'last_interaction_date': format_date_or_datetime(export_interaction.date),
                },
                {
                    'id': str(sorted_reminders[1].id),
                    'created_on': '2022-12-15T17:00:00Z',
                    'event': sorted_reminders[1].event,
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
                        'date': format_date_or_datetime(export_interaction.date),
                        'kind': str(export_interaction.kind),
                        'subject': export_interaction.subject,
                    },
                    'last_interaction_date': format_date_or_datetime(export_interaction.date),
                },
            ],
        }

    def test_get_reminders_no_team(self):
        """Should be returning reminders of interactions created by users with no DIT team"""
        interaction_adviser = AdviserFactory(dit_team=None)
        export_interaction = CompaniesInteractionFactory(created_by=interaction_adviser)

        NewExportInteractionReminderFactory.create(
            adviser=self.user,
            interaction=export_interaction,
        )

        response = self.get_response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        returned_reminder = data['results'][0]
        assert returned_reminder['interaction']['created_by']['dit_team'] is None


@freeze_time('2022-11-07T17:00:00.000000Z')
class TestNoRecentExportInteractionReminderViewset(APITestMixin, ReminderTestMixin):
    """
    Tests for the no recent export interaction reminder view.
    """

    url_name = 'api-v4:reminder:no-recent-export-interaction-reminder'
    detail_url_name = 'api-v4:reminder:no-recent-export-interaction-reminder-detail'
    factory = NoRecentExportInteractionReminderFactory
    tested_model = NoRecentExportInteractionReminder

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
        response = self.get_response
        assert response.status_code == status.HTTP_200_OK

        sorted_reminders = sorted(reminders, key=lambda x: x.pk)
        data = response.json()
        assert data == {
            'count': reminder_count,
            'next': f'http://testserver{url}?limit=2&offset=2',
            'previous': None,
            'results': [
                {
                    'id': str(sorted_reminders[0].id),
                    'created_on': '2022-11-07T17:00:00Z',
                    'last_interaction_date': format_date_or_datetime(export_interaction.date),
                    'event': sorted_reminders[0].event,
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
                        'date': format_date_or_datetime(export_interaction.date),
                        'kind': str(export_interaction.kind),
                        'subject': export_interaction.subject,
                    },
                },
                {
                    'id': str(sorted_reminders[1].id),
                    'created_on': '2022-11-07T17:00:00Z',
                    'last_interaction_date': format_date_or_datetime(export_interaction.date),
                    'event': sorted_reminders[1].event,
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
                        'date': format_date_or_datetime(export_interaction.date),
                        'kind': str(export_interaction.kind),
                        'subject': export_interaction.subject,
                    },
                },
            ],
        }

    def test_get_reminders_no_interaction(self):
        """Should return reminders for companies with no interactions"""
        reminder_count = 3
        export_company = CompanyFactory()
        reminders = NoRecentExportInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
            company=export_company,
        )
        url = reverse(self.url_name)
        response = self.get_response
        assert response.status_code == status.HTTP_200_OK

        sorted_reminders = sorted(reminders, key=lambda x: x.pk)
        data = response.json()
        assert data == {
            'count': reminder_count,
            'next': f'http://testserver{url}?limit=2&offset=2',
            'previous': None,
            'results': [
                {
                    'id': str(sorted_reminders[0].id),
                    'created_on': '2022-11-07T17:00:00Z',
                    'event': sorted_reminders[0].event,
                    'last_interaction_date': format_date_or_datetime(export_company.created_on),
                    'company': {
                        'id': str(export_company.id),
                        'name': export_company.name,
                    },
                    'interaction': None,
                },
                {
                    'id': str(sorted_reminders[1].id),
                    'created_on': '2022-11-07T17:00:00Z',
                    'event': sorted_reminders[1].event,
                    'last_interaction_date': format_date_or_datetime(export_company.created_on),
                    'company': {
                        'id': str(export_company.id),
                        'name': export_company.name,
                    },
                    'interaction': None,
                },
            ],
        }

    def test_get_reminders_no_team(self):
        """Should be returning reminders of interactions created by users with no DIT team"""
        interaction_adviser = AdviserFactory(dit_team=None)
        export_interaction = CompaniesInteractionFactory(created_by=interaction_adviser)

        NoRecentExportInteractionReminderFactory.create(
            adviser=self.user,
            interaction=export_interaction,
        )

        response = self.get_response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        returned_reminder = data['results'][0]
        assert returned_reminder['interaction']['created_by']['dit_team'] is None


@freeze_time('2022-05-05T17:00:00.000000Z')
class TestNoRecentInvestmentInteractionReminderViewset(APITestMixin, ReminderTestMixin):
    """
    Tests for the no recent investment interaction reminder view.
    """

    url_name = 'api-v4:reminder:no-recent-investment-interaction-reminder'
    detail_url_name = 'api-v4:reminder:no-recent-investment-interaction-reminder-detail'
    factory = NoRecentInvestmentInteractionReminderFactory
    tested_model = NoRecentInvestmentInteractionReminder

    def test_get_reminders(self):
        """Given some reminders, these should be returned"""
        reminder_count = 3
        reminders = NoRecentInvestmentInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        response = self.get_response
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


@freeze_time('2022-05-05T17:00:00.000000Z')
class TestUpcomingEstimatedLandDateReminderViewset(APITestMixin, ReminderTestMixin):
    """
    Tests for the upcoming estimated land date reminder view.
    """

    url_name = 'api-v4:reminder:estimated-land-date-reminder'
    detail_url_name = 'api-v4:reminder:estimated-land-date-reminder-detail'
    factory = UpcomingEstimatedLandDateReminderFactory
    tested_model = UpcomingEstimatedLandDateReminder

    def test_get_reminders(self):
        """Given some reminders, these should be returned"""
        reminder_count = 3
        reminders = UpcomingEstimatedLandDateReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        response = self.get_response
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

    def test_get_summary_of_reminders(
        self,
        investment_notifications_user_feature_group,
        export_notifications_user_feature_group,
    ):
        """Should return a summary of reminders."""
        self.user.feature_groups.set(
            [
                investment_notifications_user_feature_group,
                export_notifications_user_feature_group,
            ]
        )
        reminder_count = 3
        reminder_categories = 5  # used for finding the total number of reminders in this test
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
        NewExportInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        NewExportInteractionReminderFactory.create_batch(2)
        NoRecentExportInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        NoRecentExportInteractionReminderFactory.create_batch(2)
        total_reminders = reminder_count * reminder_categories
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            'count': total_reminders,
            'investment': {
                'estimated_land_date': reminder_count,
                'no_recent_interaction': reminder_count,
                'outstanding_propositions': reminder_count,
            },
            'export': {
                'new_interaction': reminder_count,
                'no_recent_interaction': reminder_count,
            },
        }

    def test_get_zeroes_if_no_reminders(self):
        """Should return zeroes if user does not have any reminders."""
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            'count': 0,
            'investment': {
                'estimated_land_date': 0,
                'no_recent_interaction': 0,
                'outstanding_propositions': 0,
            },
            'export': {
                'new_interaction': 0,
                'no_recent_interaction': 0,
            },
        }

    @pytest.mark.parametrize(
        'investment,export',
        (
            (False, False),
            (False, True),
            (True, False),
            (True, True),
        ),
    )
    def test_get_summary_of_reminders_with_feature_groups(
        self,
        investment,
        export,
        investment_notifications_user_feature_group,
        export_notifications_user_feature_group,
    ):
        """
        Should return a summary of reminders.

        It should return 0 for reminder category that does not have relevant feature group.
        """
        if investment:
            self.user.feature_groups.add(investment_notifications_user_feature_group)
        if export:
            self.user.feature_groups.add(export_notifications_user_feature_group)
        reminder_count = 3
        UpcomingEstimatedLandDateReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        NoRecentInvestmentInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        PropositionFactory.create_batch(
            reminder_count,
            adviser=self.user,
            status=PropositionStatus.ONGOING,
        )
        NewExportInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        NoRecentExportInteractionReminderFactory.create_batch(
            reminder_count,
            adviser=self.user,
        )
        total_reminders = reminder_count * (int(investment) * 3 + int(export) * 2)
        url = reverse(self.url_name)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            'count': total_reminders,
            'investment': {
                'estimated_land_date': reminder_count if investment else 0,
                'no_recent_interaction': reminder_count if investment else 0,
                'outstanding_propositions': reminder_count if investment else 0,
            },
            'export': {
                'new_interaction': reminder_count if export else 0,
                'no_recent_interaction': reminder_count if export else 0,
            },
        }
