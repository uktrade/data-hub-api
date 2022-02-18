"""Tests for investment views."""

from uuid import uuid4

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)
from datahub.investment.project.notification.models import InvestmentNotificationSubscription
from datahub.investment.project.notification.test.factories import (
    InvestmentNotificationSubscriptionFactory,
)
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
)
from datahub.metadata.test.factories import TeamFactory


class TestInvestmentNotificationSubscriptionView(APITestMixin):
    """
    Tests for the investment notification subscription endpoints

    These cover GET and POST /v3/investment/<project-id>/notification
    """

    def test_get_returns_401_if_not_logged_in(self, client):
        """Should return 401."""
        url = reverse(
            'api-v3:investment:notification:notification-subscription',
            kwargs={
                'project_pk': uuid4(),
            },
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_returns_401_if_not_logged_in(self, client):
        """Should return 401."""
        url = reverse(
            'api-v3:investment:notification:notification-subscription',
            kwargs={
                'project_pk': uuid4(),
            },
        )
        response = client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_empty_subscription_if_does_not_exist(self):
        """Test it returns an empty subscription even if the record does not exist."""
        project = InvestmentProjectFactory()

        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)

        with pytest.raises(InvestmentNotificationSubscription.DoesNotExist):
            InvestmentNotificationSubscription.objects.get(
                investment_project_id=project.pk,
                adviser_id=user.pk,
            )

        url = reverse(
            'api-v3:investment:notification:notification-subscription',
            kwargs={
                'project_pk': project.pk,
            },
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'estimated_land_date': [],
        }

    def test_returns_subscription(self):
        """Test that endpoint returns a notification subscription if it exists."""
        project = InvestmentProjectFactory()
        user = create_test_user(dit_team=TeamFactory())

        notification_choice = InvestmentNotificationSubscription.EstimatedLandDateNotification
        InvestmentNotificationSubscriptionFactory(
            investment_project=project,
            adviser=user,
            estimated_land_date=[
                notification_choice.ESTIMATED_LAND_DATE_30,
                notification_choice.ESTIMATED_LAND_DATE_60,
            ],
        )

        api_client = self.create_api_client(user=user)

        url = reverse(
            'api-v3:investment:notification:notification-subscription',
            kwargs={
                'project_pk': project.pk,
            },
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        expected_data = sorted(response_data['estimated_land_date'])
        assert expected_data == [
            str(notification_choice.ESTIMATED_LAND_DATE_30),
            str(notification_choice.ESTIMATED_LAND_DATE_60),
        ]

    def test_can_update_subscription(self):
        """Test that notification subscription can be updated."""
        project = InvestmentProjectFactory()
        user = create_test_user(dit_team=TeamFactory())

        notification_choice = InvestmentNotificationSubscription.EstimatedLandDateNotification
        InvestmentNotificationSubscriptionFactory(
            investment_project=project,
            adviser=user,
            estimated_land_date=[
                notification_choice.ESTIMATED_LAND_DATE_30,
                notification_choice.ESTIMATED_LAND_DATE_60,
            ],
        )

        api_client = self.create_api_client(user=user)

        url = reverse(
            'api-v3:investment:notification:notification-subscription',
            kwargs={
                'project_pk': project.pk,
            },
        )
        notification_choice = InvestmentNotificationSubscription.EstimatedLandDateNotification
        response = api_client.post(url, data={
            'estimated_land_date': [
                str(notification_choice.ESTIMATED_LAND_DATE_30),
            ],
        })
        assert response.status_code == status.HTTP_200_OK

        subscription = InvestmentNotificationSubscription.objects.get(
            investment_project_id=project.pk,
            adviser_id=user.pk,
        )
        assert subscription.estimated_land_date == [
            notification_choice.ESTIMATED_LAND_DATE_30,
        ]

    def test_cannot_update_subscription_with_unknown_parameter(self):
        """Test that notification subscription cannot be updated with an unknown parameter."""
        project = InvestmentProjectFactory()
        user = create_test_user(dit_team=TeamFactory())

        notification_choice = InvestmentNotificationSubscription.EstimatedLandDateNotification

        InvestmentNotificationSubscriptionFactory(
            investment_project=project,
            adviser=user,
            estimated_land_date=[
                notification_choice.ESTIMATED_LAND_DATE_30,
                notification_choice.ESTIMATED_LAND_DATE_60,
            ],
        )

        api_client = self.create_api_client(user=user)

        url = reverse(
            'api-v3:investment:notification:notification-subscription',
            kwargs={
                'project_pk': project.pk,
            },
        )
        response = api_client.post(url, data={
            'estimated_land_date': [
                'every_day',
            ],
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'estimated_land_date': ['"every_day" is not a valid choice.']}
