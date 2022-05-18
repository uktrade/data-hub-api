from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.core.test_utils import APITestMixin
from datahub.reminder.test.factories import (
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


@freeze_time('2022-05-05T17:00:00.000000Z')
class TestNoRecentInvestmentInteractionReminderViewset(APITestMixin):
    """
    Tests for the no recent investment interation reminder view.
    """

    url_name = 'api-v4:reminder:no-recent-investment-interaction-reminder'

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
        assert results[0] == {
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


@freeze_time('2022-05-05T17:00:00.000000Z')
class TestUpcomingEstimatedLandDateReminderViewset(APITestMixin):
    """
    Tests for the upcoming estimated land date reminder view.
    """

    url_name = 'api-v4:reminder:estimated-land-date-reminder'

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
        assert results[0] == {
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
