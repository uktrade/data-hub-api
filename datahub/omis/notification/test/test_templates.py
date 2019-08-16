import pytest
from dateutil.parser import parse as dateutil_parse
from django.conf import settings

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import UKRegion
from datahub.omis.market.models import Market
from datahub.omis.notification.client import Notify
from datahub.omis.order.test.factories import (
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderWithOpenQuoteFactory,
)
from datahub.omis.region.models import UKRegionalSettings


pytestmark = pytest.mark.django_db


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

    def test_order_info(self, settings, notify_client):
        """
        Test the order info template.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        notify.order_info(OrderFactory(), what_happened='', why='')

    def test_order_created(self, settings, notify_client):
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

    def test_you_have_been_added_for_adviser(self, settings, notify_client):
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

    def test_you_have_been_removed_for_adviser(self, settings, notify_client):
        """
        Test the notification for when an adviser is removed from an order.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderFactory()

        notify.adviser_removed(order=order, adviser=AdviserFactory())

    def test_order_paid(self, settings, notify_client):
        """
        Test templates of order paid for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderPaidFactory()

        notify.order_paid(order)

    def test_order_completed(self, settings, notify_client):
        """
        Test templates of order completed for advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderCompleteFactory()

        notify.order_completed(order)

    def test_order_cancelled(self, settings, notify_client):
        """
        Test templates of order cancelled for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderWithOpenQuoteFactory()

        notify.order_cancelled(order)

    def test_quote_sent(self, settings, notify_client):
        """
        Test templates of quote sent for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderWithOpenQuoteFactory()

        notify.quote_generated(order)

    def test_quote_accepted(self, settings, notify_client):
        """
        Test templates of quote accepted for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderPaidFactory()

        notify.quote_accepted(order)

    def test_quote_cancelled(self, settings, notify_client):
        """
        Test templates of quote cancelled for customer and advisers.
        If the template variables have been changed in GOV.UK notifications this
        is going to raise HTTPError (400 - Bad Request).
        """
        settings.OMIS_NOTIFICATION_API_KEY = settings.OMIS_NOTIFICATION_TEST_API_KEY
        notify = Notify()

        order = OrderWithOpenQuoteFactory()

        notify.quote_cancelled(order, by=AdviserFactory())
