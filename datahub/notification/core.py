import warnings
from unittest import mock

from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient

from datahub.notification.constants import DEFAULT_SERVICE_NAME, NOTIFY_KEYS


class NotifyGateway:
    """
    For accessing underlying GOVUK notification service.
    """

    def __init__(self):
        """
        Init underlying notification client(s).
        """
        self._initialise_clients()

    def _initialise_clients(self):
        clients = {}
        for service_name, api_key_setting_name in NOTIFY_KEYS.items():
            api_key = getattr(settings, api_key_setting_name, None)
            if api_key:
                clients[service_name] = NotificationsAPIClient(api_key)
            else:
                client = mock.Mock(spec_set=NotificationsAPIClient)
                client.send_email_notification.return_value = {'id': 'abc123'}
                clients[service_name] = client
                warnings.warn(
                    f'`settings.{api_key_setting_name}` not specified therefore notifications '
                    "will be mocked. You might want to change this if it's not a testing or "
                    'development environment.',
                    RuntimeWarning,
                    stacklevel=2,
                )
        self.clients = clients

    def send_email_notification(
        self,
        recipient_email,
        template_identifier,
        context=None,
        notify_service_name=None,
    ):
        """
        Send an email notification using the GOVUK notification service.
        """
        # TODO: the default notify service name should be in a setting, not a constant.
        # This will be fixed when we fully move over omis notifications from its
        # own notification package to this app
        if not notify_service_name:
            notify_service_name = DEFAULT_SERVICE_NAME
        client = self.clients[notify_service_name]
        if not context:
            context = {}
        return client.send_email_notification(
            email_address=recipient_email,
            template_id=template_identifier,
            personalisation=context,
        )


notify_gateway = NotifyGateway()
