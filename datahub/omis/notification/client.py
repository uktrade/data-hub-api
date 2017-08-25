import warnings
from logging import getLogger
from unittest import mock

from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient
from raven.contrib.django.raven_compat.models import client as raven_client

from datahub.core.utils import executor
from datahub.omis.market.models import Market

from .constants import Template


logger = getLogger(__name__)


def send_email(client, *args, **kwargs):
    """Send email and catch potential errors."""
    try:
        client.send_email_notification(*args, **kwargs)
    except:  # noqa: B901
        logger.exception('Error while sending a notification email.')
        raven_client.captureException()
        raise


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
                settings.OMIS_NOTIFICATION_API_KEY
            )
        else:
            self.client = mock.Mock(spec_set=NotificationsAPIClient)
            warnings.warn(
                '`settings.OMIS_NOTIFICATION_API_KEY` not specified therefore all '
                'OMIS notifications will be mocked. '
                'You might want to change this if it\'s not a '
                'testing or development environment.',
                RuntimeWarning,
                stacklevel=2
            )

    def _send_email(self, *args, **kwargs):
        """Send email in a separate thread."""
        executor.submit(send_email, self.client, *args, **kwargs)

    def _prepare_personalisation(self, order, data=None):
        """Prepare the personalisation data with common values."""
        return {
            'order ref': order.reference,
            'company name': order.company.name,
            'embedded link': order.get_datahub_frontend_url(),
            **(data or {})
        }

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
                    'recipient name': to_name or receipient_email
                }
            )
        )

    def order_created(self, order):
        """
        Send a notification of an order just created.
        This usually alerts the related overseas manager if it exists or it falls back
        to notifying the OMIS admin that something is not right.
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
                template_id=Template.order_created.value,
                personalisation=self._prepare_personalisation(
                    order,
                    {
                        'recipient name': manager_email,
                        'creator': order.created_by.name if order.created_by else None,
                    }
                )
            )
        else:
            data = {
                'order': order,
                'what_happened': 'We couldn\'t notify the overseas manager'
            }

            if not market:
                data['why'] = (
                    f'country {order.primary_market.name} '
                    'doesn\'t have an OMIS market defined'
                )
            else:
                data['why'] = (
                    f'no manager email for market {order.primary_market.name} '
                    'could be found. Please log into the admin and add one'
                )

            self.order_info(**data)


notify = Notify()
