from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.core.test_utils import APITestMixin
from datahub.reminder.test.factories import (
    NoRecentInvestmentInteractionSubscriptionFactory,
    UpcomingEstimatedLandDateSubscriptionFactory,
)


class TestNoRecentInvestmentInteractionSubscriptionViewset(APITestMixin):
    """
    Tests for the no recent investment interation subscription view.
    """

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse('api-v4:reminder:no-recent-investment-interaction-subscription')
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_subscription_not_present(self):
        """Given the current user does not have a subscription, make an empty one"""
        url = reverse('api-v4:reminder:no-recent-investment-interaction-subscription')
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
        url = reverse('api-v4:reminder:no-recent-investment-interaction-subscription')
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

    def test_not_authed(self):
        """Should return Unauthorised"""
        url = reverse('api-v4:reminder:estimated-land-date-subscription')
        api_client = APIClient()
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_subscription_not_present(self):
        """Given the current user does not have a subscription, make an empty one"""
        url = reverse('api-v4:reminder:estimated-land-date-subscription')
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
        url = reverse('api-v4:reminder:estimated-land-date-subscription')
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'reminder_days': [10, 20, 40],
            'email_reminders_enabled': True,
        }
