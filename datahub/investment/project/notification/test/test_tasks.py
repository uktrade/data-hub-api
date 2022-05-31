from unittest import mock
from uuid import uuid4

import factory
import pytest
from dateutil.relativedelta import relativedelta
from django.test.utils import override_settings
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import InvestmentProjectStage
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.investment.project import (
    INVESTMENT_ESTIMATED_LAND_DATE_NOTIFICATION_FEATURE_FLAG_NAME,
)
from datahub.investment.project.notification.models import InvestmentNotificationSubscription
from datahub.investment.project.notification.tasks import (
    get_subscriptions_for_estimated_land_date,
    send_estimated_land_date_task,
)
from datahub.investment.project.notification.test.factories import (
    InvestmentNotificationSubscriptionFactory,
)
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
)
from datahub.notification.constants import NotifyServiceName

pytestmark = pytest.mark.django_db

estimated_land_date_notification = InvestmentNotificationSubscription.EstimatedLandDateNotification


@pytest.fixture
def mock_notify_adviser_by_email(monkeypatch):
    """
    Mocks the notify_adviser_by_email function.
    """
    mock_notify_adviser_by_email = mock.Mock()
    monkeypatch.setattr(
        'datahub.investment.project.notification.tasks.notify_adviser_by_email',
        mock_notify_adviser_by_email,
    )
    return mock_notify_adviser_by_email


@pytest.fixture
def mock_statsd(monkeypatch):
    """
    Returns a mock statsd client instance.
    """
    mock_statsd = mock.Mock()
    monkeypatch.setattr(
        'datahub.investment.project.notification.tasks.statsd',
        mock_statsd,
    )
    return mock_statsd


@pytest.fixture()
def investment_estimated_land_date_notification_feature_flag():
    """
    Creates the investment estimated land date notification feature flag.
    """
    yield FeatureFlagFactory(code=INVESTMENT_ESTIMATED_LAND_DATE_NOTIFICATION_FEATURE_FLAG_NAME)


@pytest.mark.usefixtures('local_memory_cache')
class TestInvestmentNotificationSubscriptionTasks:
    """Test investment notification subscription tasks."""

    @pytest.mark.parametrize(
        'notification_type',
        (
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_30.value
            ),
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_60.value
            ),
        ),
    )
    def test_get_subscriptions_for_estimated_land_date(self, notification_type):
        """Tests that query returns correct subscriptions."""
        adviser = AdviserFactory()
        future_estimated_land_date = now() + relativedelta(days=int(notification_type))
        projects = [
            InvestmentProjectFactory(
                project_manager=adviser,
                estimated_land_date=future_estimated_land_date,
            ),
            InvestmentProjectFactory(
                project_manager=adviser,
                estimated_land_date=future_estimated_land_date - relativedelta(days=1),
            ),
            InvestmentProjectFactory(
                project_manager=adviser,
                estimated_land_date=future_estimated_land_date + relativedelta(days=1),
            ),
        ]
        InvestmentNotificationSubscriptionFactory.create_batch(
            len(projects),
            investment_project=factory.Iterator(projects),
            adviser=adviser,
            estimated_land_date=[notification_type],
        )

        subscriptions = get_subscriptions_for_estimated_land_date(notification_type)
        assert subscriptions.count() == 1
        assert subscriptions[0].adviser == adviser
        assert subscriptions[0].investment_project == projects[0]
        assert notification_type in subscriptions[0].estimated_land_date

    @pytest.mark.parametrize(
        'notification_type',
        (
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_30.value
            ),
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_60.value
            ),
        ),
    )
    def test_subscriptions_dont_include_verify_win_and_won_projects(self, notification_type):
        """Tests that query returns subscriptions excluding verify win and won projects."""
        adviser = AdviserFactory()
        future_estimated_land_date = now() + relativedelta(days=int(notification_type))
        projects = [
            InvestmentProjectFactory(
                project_manager=adviser,
                estimated_land_date=future_estimated_land_date,
            ),
            InvestmentProjectFactory(
                project_manager=adviser,
                estimated_land_date=future_estimated_land_date,
                stage_id=InvestmentProjectStage.verify_win.value.id,
            ),
            InvestmentProjectFactory(
                project_manager=adviser,
                estimated_land_date=future_estimated_land_date,
                stage_id=InvestmentProjectStage.won.value.id,
            ),
        ]
        InvestmentNotificationSubscriptionFactory.create_batch(
            len(projects),
            investment_project=factory.Iterator(projects),
            adviser=adviser,
            estimated_land_date=[notification_type],
        )

        subscriptions = get_subscriptions_for_estimated_land_date(notification_type)
        assert subscriptions.count() == 1
        assert subscriptions[0].adviser == adviser
        assert subscriptions[0].investment_project == projects[0]
        assert notification_type in subscriptions[0].estimated_land_date

    @pytest.mark.parametrize(
        'notification_type,user_type',
        (
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_30.value,
                'project_manager',
            ),
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_60.value,
                'project_manager',
            ),
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_30.value,
                'client_relationship_manager',
            ),
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_60.value,
                'client_relationship_manager',
            ),
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_30.value,
                'project_assurance_adviser',
            ),
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_60.value,
                'project_assurance_adviser',
            ),
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_30.value,
                'referral_source_adviser',
            ),
            (
                estimated_land_date_notification.ESTIMATED_LAND_DATE_60.value,
                'referral_source_adviser',
            ),
        ),
    )
    def test_sends_investment_notification_with_feature_flag(
        self,
        notification_type,
        user_type,
        investment_estimated_land_date_notification_feature_flag,
        mock_notify_adviser_by_email,
        mock_statsd,
    ):
        """
        Test that a notification will be sent for each notification type and user.
        """
        adviser = AdviserFactory()
        future_estimated_land_date = now() + relativedelta(days=int(notification_type))
        project = InvestmentProjectFactory(
            **{user_type: adviser},
            estimated_land_date=future_estimated_land_date,
        )
        InvestmentProjectFactory(
            **{user_type: adviser},
            estimated_land_date=future_estimated_land_date - relativedelta(days=1),
        )
        InvestmentProjectFactory(
            **{user_type: adviser},
            estimated_land_date=future_estimated_land_date + relativedelta(days=1),
        )
        InvestmentNotificationSubscriptionFactory(
            investment_project=project,
            adviser=adviser,
            estimated_land_date=[notification_type],
        )

        template_id = str(uuid4())
        with override_settings(
            INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_TEMPLATE_ID=template_id,
        ):
            send_estimated_land_date_task()

            mock_notify_adviser_by_email.assert_called_once_with(
                adviser,
                template_id,
                {
                    'project_details_url': f'{project.get_absolute_url()}/details',
                    'project_subscription_url': f'{project.get_absolute_url()}/notifications/'
                                                'estimated-land-date',
                    'investor_company_name': project.investor_company.name,
                    'project_name': project.name,
                    'project_code': project.project_code,
                    'project_status': project.status.capitalize(),
                    'project_stage': project.stage.name,
                    'estimated_land_date': project.estimated_land_date.strftime('%-d %B %Y'),
                },
                NotifyServiceName.investment,
            )
            mock_statsd.incr.assert_called_once_with(
                f'send_investment_notification.{notification_type}',
            )

    def test_doesnt_send_investment_notification_without_feature_flag(
        self,
        mock_notify_adviser_by_email,
    ):
        """
        Tests that notifications are not sent if the feature flag is not enabled.
        """
        notification_type = estimated_land_date_notification.ESTIMATED_LAND_DATE_30.value
        adviser = AdviserFactory()
        future_estimated_land_date = now() + relativedelta(days=int(notification_type))
        project = InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )
        InvestmentNotificationSubscriptionFactory(
            investment_project=project,
            adviser=adviser,
            estimated_land_date=[notification_type],
        )

        template_id = str(uuid4())
        with override_settings(
            INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_TEMPLATE_ID=template_id,
        ):
            send_estimated_land_date_task()

            mock_notify_adviser_by_email.assert_not_called()

    def test_does_not_send_multiple_notifications(
        self,
        investment_estimated_land_date_notification_feature_flag,
        mock_notify_adviser_by_email,
    ):
        """
        Test that the send_estimate_land_date_task will not send multiple notifications if
        called multiple times.
        """
        notification_type = estimated_land_date_notification.ESTIMATED_LAND_DATE_30.value
        adviser = AdviserFactory()
        future_estimated_land_date = now() + relativedelta(days=int(notification_type))
        project = InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )
        InvestmentNotificationSubscriptionFactory(
            investment_project=project,
            adviser=adviser,
            estimated_land_date=[notification_type],
        )

        template_id = str(uuid4())
        with override_settings(
            INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_TEMPLATE_ID=template_id,
        ):
            send_estimated_land_date_task()
            send_estimated_land_date_task()
            send_estimated_land_date_task()
            send_estimated_land_date_task()
            send_estimated_land_date_task()

            mock_notify_adviser_by_email.assert_called_once()
