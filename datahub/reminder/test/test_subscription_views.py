import pytest

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.core.test_utils import APITestMixin
from datahub.feature_flag.test.factories import UserFeatureFlagGroupFactory
from datahub.reminder import (
    EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME,
)
from datahub.reminder.test.factories import (
    NewExportInteractionSubscriptionFactory,
    NoRecentExportInteractionSubscriptionFactory,
    NoRecentInvestmentInteractionSubscriptionFactory,
    TaskAssignedToMeFromOthersSubscriptionFactory,
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
        TaskAssignedToMeFromOthersSubscriptionFactory(
            adviser=self.user,
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
