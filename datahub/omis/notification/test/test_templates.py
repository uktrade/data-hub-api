import pytest
from dateutil.parser import parse as dateutil_parse
from django.conf import settings
from django.test.utils import override_settings

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import UKRegion
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.notification.core import NotifyGateway
from datahub.notification.tasks import send_email_notification
from datahub.omis.market.models import Market
from datahub.omis.notification.client import Notify
from datahub.omis.notification.constants import OMIS_USE_NOTIFICATION_APP_FEATURE_FLAG_NAME
from datahub.omis.order.test.factories import (
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderWithOpenQuoteFactory,
)
from datahub.omis.region.models import UKRegionalSettings


pytestmark = pytest.mark.django_db


@pytest.fixture
def notify_task_return_value_tracker(track_return_values):
    """
    Attaches and returns a return value tracker for send email notification
    tasks.
    """
    return track_return_values(send_email_notification, 'apply_async')


@pytest.fixture
def end_to_end_notify(monkeypatch, settings):
    """
    A fixture for a notify client which uses the new datahub.notification app
    under the hood and calls through to the GOVUK notify service (with
    settings.OMIS_NOTIFICATION_TEST_API_KEY).

    By contrast, our other test cases will use mocked clients so that no actual
    web requests are made to GOVUK notify.
    """
    with override_settings(OMIS_NOTIFICATION_API_KEY=settings.OMIS_NOTIFICATION_TEST_API_KEY):
        monkeypatch.setattr(
            'datahub.notification.tasks.notify_gateway',
            NotifyGateway(),
        )
        FeatureFlagFactory(code=OMIS_USE_NOTIFICATION_APP_FEATURE_FLAG_NAME)
        yield Notify()


@pytest.mark.skipif(
    not settings.OMIS_NOTIFICATION_TEST_API_KEY,
    reason='`settings.OMIS_NOTIFICATION_TEST_API_KEY` not set (optional).',
)
@pytest.mark.usefixtures('synchronous_thread_pool')
class TestTemplates:
    """
    These tests are going to be run only if `OMIS_NOTIFICATION_TEST_API_KEY` is set
    and it's meant to check that the templates in GOV.UK notifications have not been
    changed.
    If `OMIS_NOTIFICATION_TEST_API_KEY` is not set they will not run as they are
    not strictly mandatory.
    """

    def _assert_tasks_successful(self, task_count, return_value_tracker):
        task_results = return_value_tracker.return_values
        assert len(task_results) == task_count
        for task_result in task_results:
            try:
                task_result.get()
            except Exception as exc:
                pytest.fail(f'Notify task raised an exception {exc}')

    def test_order_info(self, end_to_end_notify, notify_task_return_value_tracker):
        """
        Test the order info template.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        end_to_end_notify.order_info(OrderFactory(), what_happened='', why='')
        self._assert_tasks_successful(1, notify_task_return_value_tracker)

    def test_order_created(self, end_to_end_notify, notify_task_return_value_tracker):
        """
        Test the order created template.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        market = Market.objects.first()
        market.manager_email = 'test@test.com'
        market.save()

        UKRegionalSettings.objects.create(
            uk_region_id=UKRegion.london.value.id,
            manager_emails=['reg_test@test.com'],
        )

        order = OrderFactory(
            primary_market_id=market.country.pk,
            uk_region_id=UKRegion.london.value.id,
        )

        end_to_end_notify.order_created(order)
        self._assert_tasks_successful(2, notify_task_return_value_tracker)

    def test_you_have_been_added_for_adviser(
        self,
        end_to_end_notify,
        notify_task_return_value_tracker,
    ):
        """
        Test the notification for when an adviser is added to an order.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        order = OrderFactory()

        end_to_end_notify.adviser_added(
            order=order,
            adviser=AdviserFactory(),
            by=AdviserFactory(),
            creation_date=dateutil_parse('2017-05-18'),
        )
        self._assert_tasks_successful(1, notify_task_return_value_tracker)

    def test_you_have_been_removed_for_adviser(
        self,
        end_to_end_notify,
        notify_task_return_value_tracker,
    ):
        """
        Test the notification for when an adviser is removed from an order.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        order = OrderFactory()

        end_to_end_notify.adviser_removed(order=order, adviser=AdviserFactory())
        self._assert_tasks_successful(1, notify_task_return_value_tracker)

    def test_order_paid(self, end_to_end_notify, notify_task_return_value_tracker):
        """
        Test templates of order paid for customer and advisers.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        order = OrderPaidFactory()

        end_to_end_notify.order_paid(order)
        self._assert_tasks_successful(2, notify_task_return_value_tracker)

    def test_order_completed(self, end_to_end_notify, notify_task_return_value_tracker):
        """
        Test templates of order completed for advisers.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        order = OrderCompleteFactory()

        end_to_end_notify.order_completed(order)
        self._assert_tasks_successful(1, notify_task_return_value_tracker)

    def test_order_cancelled(self, end_to_end_notify, notify_task_return_value_tracker):
        """
        Test templates of order cancelled for customer and advisers.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        order = OrderWithOpenQuoteFactory()

        end_to_end_notify.order_cancelled(order)
        self._assert_tasks_successful(2, notify_task_return_value_tracker)

    def test_quote_sent(self, end_to_end_notify, notify_task_return_value_tracker):
        """
        Test templates of quote sent for customer and advisers.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        order = OrderWithOpenQuoteFactory()

        end_to_end_notify.quote_generated(order)
        self._assert_tasks_successful(2, notify_task_return_value_tracker)

    def test_quote_accepted(self, end_to_end_notify, notify_task_return_value_tracker):
        """
        Test templates of quote accepted for customer and advisers.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        order = OrderPaidFactory()

        end_to_end_notify.quote_accepted(order)
        self._assert_tasks_successful(2, notify_task_return_value_tracker)

    def test_quote_cancelled(self, end_to_end_notify, notify_task_return_value_tracker):
        """
        Test templates of quote cancelled for customer and advisers.
        If the template variables have been changed in GOV.UK notifications the
        celery task will be unsuccessful.
        """
        order = OrderWithOpenQuoteFactory()

        end_to_end_notify.quote_cancelled(order, by=AdviserFactory())
        self._assert_tasks_successful(2, notify_task_return_value_tracker)


@pytest.mark.skipif(
    not settings.OMIS_NOTIFICATION_TEST_API_KEY,
    reason='`settings.OMIS_NOTIFICATION_TEST_API_KEY` not set (optional).',
)
@pytest.mark.usefixtures('synchronous_thread_pool')
class TestTemplatesLegacyOMISNotification:
    """
    TODO: This will need removing when we switch over fully to using the
    datahub.notification app.

    These tests are going to be run only if `OMIS_NOTIFICATION_TEST_API_KEY` is set
    and it's meant to check that the templates in GOV.UK notifications have not been
    changed.
    If `OMIS_NOTIFICATION_TEST_API_KEY` is not set they will not run as they are
    not strictly mandatory.
    """

    def test_order_info(self, settings):
        """
        Test the order info template.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        notify.order_info(OrderFactory(), what_happened='', why='')

    def test_order_created(self, settings):
        """
        Test the order created template.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        market = Market.objects.first()
        market.manager_email = 'test@test.com'
        market.save()

        UKRegionalSettings.objects.create(
            uk_region_id=UKRegion.london.value.id,
            manager_emails=['reg_test@test.com'],
        )

        order = OrderFactory(
            primary_market_id=market.country.pk,
            uk_region_id=UKRegion.london.value.id,
        )

        notify.order_created(order)

    def test_you_have_been_added_for_adviser(self, settings):
        """
        Test the notification for when an adviser is added to an order.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderFactory()

        notify.adviser_added(
            order=order,
            adviser=AdviserFactory(),
            by=AdviserFactory(),
            creation_date=dateutil_parse('2017-05-18'),
        )

    def test_you_have_been_removed_for_adviser(self, settings):
        """
        Test the notification for when an adviser is removed from an order.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderFactory()

        notify.adviser_removed(order=order, adviser=AdviserFactory())

    def test_order_paid(self, settings):
        """
        Test templates of order paid for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderPaidFactory()

        notify.order_paid(order)

    def test_order_completed(self, settings):
        """
        Test templates of order completed for advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderCompleteFactory()

        notify.order_completed(order)

    def test_order_cancelled(self, settings):
        """
        Test templates of order cancelled for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderWithOpenQuoteFactory()

        notify.order_cancelled(order)

    def test_quote_sent(self, settings):
        """
        Test templates of quote sent for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderWithOpenQuoteFactory()

        notify.quote_generated(order)

    def test_quote_accepted(self, settings):
        """
        Test templates of quote accepted for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderPaidFactory()

        notify.quote_accepted(order)

    def test_quote_cancelled(self, settings):
        """
        Test templates of quote cancelled for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderWithOpenQuoteFactory()

        notify.quote_cancelled(order, by=AdviserFactory())
