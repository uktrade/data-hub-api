import itertools
import warnings
from logging import getLogger
from unittest import mock

from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient

from datahub.core.thread_pool import submit_to_thread_pool
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.notification.constants import NotifyServiceName
from datahub.notification.notify import notify_by_email
from datahub.omis.market.models import Market
from datahub.omis.notification.constants import (
    OMIS_USE_NOTIFICATION_APP_FEATURE_FLAG_NAME,
    Template,
)
from datahub.omis.region.models import UKRegionalSettings


logger = getLogger(__name__)


def send_email(client, **kwargs):
    """Send email and catch potential errors."""
    client.send_email_notification(**kwargs)


class Notify:
    """
    Used to send notifications when something happens to an order.

    The GOV.UK notification key can be set in settings.OMIS_NOTIFICATION_API_KEY,
    if empty, the client will be mocked and no notification will be sent.

    E.g.
        notify = Notify()
        notify.order_created(order)
    """

    def __init__(self):
        """Init underlying notification client."""
        if settings.OMIS_NOTIFICATION_API_KEY:
            self.client = NotificationsAPIClient(
                settings.OMIS_NOTIFICATION_API_KEY,
            )
        else:
            self.client = mock.Mock(spec_set=NotificationsAPIClient)
            warnings.warn(
                '`settings.OMIS_NOTIFICATION_API_KEY` not specified therefore all '
                'OMIS notifications will be mocked. '
                "You might want to change this if it's not a "
                'testing or development environment.',
                RuntimeWarning,
                stacklevel=2,
            )

    def _send_email(self, **data):
        """Send email in a separate thread."""
        # override recipient if needed
        if settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL:
            data['email_address'] = settings.OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL

        use_notification_app = is_feature_flag_active(OMIS_USE_NOTIFICATION_APP_FEATURE_FLAG_NAME)
        if use_notification_app:
            notify_by_email(
                data['email_address'],
                data['template_id'],
                data.get('personalisation'),
                NotifyServiceName.omis,
            )
        else:
            submit_to_thread_pool(send_email, self.client, **data)

    def _prepare_personalisation(self, order, data=None):
        """Prepare the personalisation data with common values."""
        if order.primary_market:
            primary_market = order.primary_market.name
        else:
            primary_market = 'Unknown market'

        return {
            'order ref': order.reference,
            'company name': order.company.name,
            'embedded link': order.get_datahub_frontend_url(),
            'primary market': primary_market,
            'omis team email': settings.OMIS_GENERIC_CONTACT_EMAIL,
            **(data or {}),
        }

    def _get_all_advisers(self, order):
        """
        :returns: all advisers on the order
        """
        return itertools.chain(
            (item.adviser for item in order.assignees.all()),
            (item.adviser for item in order.subscribers.all()),
        )

    def order_info(self, order, what_happened, why, to_email=None, to_name=None):
        """
        Send a notification of type info related to the order `order`
        specifying what happened, the reason and optionally who to send it to.
        """
        receipient_email = to_email or settings.OMIS_NOTIFICATION_ADMIN_EMAIL

        self._send_email(
            email_address=receipient_email,
            template_id=Template.generic_order_info.value,
            personalisation=self._prepare_personalisation(
                order,
                {
                    'what has happened': what_happened,
                    'reason': why,
                    'recipient name': to_name or receipient_email,
                },
            ),
        )

    def _order_created_for_post_managers(self, order):
        """
        Notify the related overseas manager that a new order has been created
        if that manager exists or fall back to notifying the OMIS admin
        that something is not right.
        """
        try:
            market = order.primary_market.market
            manager_email = market.manager_email
        except Market.DoesNotExist:
            market = None
            manager_email = ''

        if manager_email:
            self._send_email(
                email_address=manager_email,
                template_id=Template.order_created_for_post_manager.value,
                personalisation=self._prepare_personalisation(
                    order,
                    {
                        'recipient name': manager_email,
                        'creator': order.created_by.name if order.created_by else None,
                    },
                ),
            )
        else:
            data = {
                'order': order,
                'what_happened': "We couldn't notify the overseas manager",
            }

            if not market:
                data['why'] = (
                    f'country {order.primary_market.name} '
                    "doesn't have an OMIS market defined"
                )
            else:
                data['why'] = (
                    f'no manager email for market {order.primary_market.name} '
                    'could be found. Please log into the admin and add one'
                )

            self.order_info(**data)

    def _order_created_for_regional_managers(self, order):
        """
        Notify the related regional managers that a new order has been created.
        """
        # no UK region specified for this order => skip
        if not order.uk_region:
            return

        # no settings for this UK region => skip
        try:
            regional_settings = order.uk_region.omis_settings
        except UKRegionalSettings.DoesNotExist:
            return

        # no email addresses for this UK region => skip
        if not regional_settings.manager_emails:
            return

        for manager_email in regional_settings.manager_emails:
            self._send_email(
                email_address=manager_email,
                template_id=Template.order_created_for_regional_manager.value,
                personalisation=self._prepare_personalisation(
                    order,
                    {
                        'recipient name': manager_email,
                        'creator': order.created_by.name if order.created_by else None,
                    },
                ),
            )

    def order_created(self, order):
        """
        Notify post managers and regional managers that a new order has been created.
        """
        self._order_created_for_post_managers(order)
        self._order_created_for_regional_managers(order)

    def adviser_added(self, order, adviser, by, creation_date):
        """Send a notification when an adviser is added to an order."""
        self._send_email(
            email_address=adviser.get_current_email(),
            template_id=Template.you_have_been_added_for_adviser.value,
            personalisation=self._prepare_personalisation(
                order,
                {
                    'recipient name': adviser.name,
                    'creator': by.name,
                    'creation date': creation_date.strftime('%d/%m/%Y'),
                },
            ),
        )

    def adviser_removed(self, order, adviser):
        """Send a notification when an adviser is removed from an order."""
        self._send_email(
            email_address=adviser.get_current_email(),
            template_id=Template.you_have_been_removed_for_adviser.value,
            personalisation=self._prepare_personalisation(
                order, {'recipient name': adviser.name},
            ),
        )

    def order_paid(self, order):
        """
        Send a notification to the customer and the advisers
        that the order has just been marked as paid.
        """
        #  notify customer
        self._send_email(
            email_address=order.get_current_contact_email(),
            template_id=Template.order_paid_for_customer.value,
            personalisation=self._prepare_personalisation(
                order,
                {
                    'recipient name': order.contact.name,
                    'embedded link': order.get_public_facing_url(),
                },
            ),
        )

        #  notify advisers
        for adviser in self._get_all_advisers(order):
            self._send_email(
                email_address=adviser.get_current_email(),
                template_id=Template.order_paid_for_adviser.value,
                personalisation=self._prepare_personalisation(
                    order, {'recipient name': adviser.name},
                ),
            )

    def order_completed(self, order):
        """
        Send a notification to the advisers that the order has
        just been marked as completed.
        """
        for adviser in self._get_all_advisers(order):
            self._send_email(
                email_address=adviser.get_current_email(),
                template_id=Template.order_completed_for_adviser.value,
                personalisation=self._prepare_personalisation(
                    order, {'recipient name': adviser.name},
                ),
            )

    def order_cancelled(self, order):
        """
        Send a notification to the customer and the advisers
        that the order has just been cancelled.
        """
        #  notify customer
        self._send_email(
            email_address=order.get_current_contact_email(),
            template_id=Template.order_cancelled_for_customer.value,
            personalisation=self._prepare_personalisation(
                order,
                {
                    'recipient name': order.contact.name,
                    'embedded link': order.get_public_facing_url(),
                },
            ),
        )

        #  notify advisers
        for adviser in self._get_all_advisers(order):
            self._send_email(
                email_address=adviser.get_current_email(),
                template_id=Template.order_cancelled_for_adviser.value,
                personalisation=self._prepare_personalisation(
                    order, {'recipient name': adviser.name},
                ),
            )

    def quote_generated(self, order):
        """
        Send a notification to the customer and the advisers
        that a quote has just been created and needs to be accepted.
        """
        #  notify customer
        self._send_email(
            email_address=order.get_current_contact_email(),
            template_id=Template.quote_sent_for_customer.value,
            personalisation=self._prepare_personalisation(
                order,
                {
                    'recipient name': order.contact.name,
                    'embedded link': order.get_public_facing_url(),
                },
            ),
        )

        #  notify advisers
        for adviser in self._get_all_advisers(order):
            self._send_email(
                email_address=adviser.get_current_email(),
                template_id=Template.quote_sent_for_adviser.value,
                personalisation=self._prepare_personalisation(
                    order, {'recipient name': adviser.name},
                ),
            )

    def quote_accepted(self, order):
        """
        Send a notification to the customer and the advisers
        that a quote has just been accepted.
        """
        #  notify customer
        self._send_email(
            email_address=order.get_current_contact_email(),
            template_id=Template.quote_accepted_for_customer.value,
            personalisation=self._prepare_personalisation(
                order,
                {
                    'recipient name': order.contact.name,
                    'embedded link': order.get_public_facing_url(),
                },
            ),
        )

        #  notify advisers
        for adviser in self._get_all_advisers(order):
            self._send_email(
                email_address=adviser.get_current_email(),
                template_id=Template.quote_accepted_for_adviser.value,
                personalisation=self._prepare_personalisation(
                    order, {'recipient name': adviser.name},
                ),
            )

    def quote_cancelled(self, order, by):
        """
        Send a notification to the customer and the advisers
        that a quote has just been cancelled.
        """
        #  notify customer
        self._send_email(
            email_address=order.get_current_contact_email(),
            template_id=Template.quote_cancelled_for_customer.value,
            personalisation=self._prepare_personalisation(
                order,
                {
                    'recipient name': order.contact.name,
                    'embedded link': order.get_public_facing_url(),
                },
            ),
        )

        #  notify advisers
        for adviser in self._get_all_advisers(order):
            self._send_email(
                email_address=adviser.get_current_email(),
                template_id=Template.quote_cancelled_for_adviser.value,
                personalisation=self._prepare_personalisation(
                    order,
                    {
                        'recipient name': adviser.name,
                        'canceller': by.name,
                    },
                ),
            )


notify = Notify()
