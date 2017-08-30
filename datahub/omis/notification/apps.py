from django.apps import AppConfig


class NotificationConfig(AppConfig):
    """Django App Config for the OMIS Notification app."""

    name = 'datahub.omis.notification'
    label = 'omis-notification'  # namespaced app. Use this e.g. when migrating

    def ready(self):
        """Registers the signals for this app.

        This is the preferred way to register signals in the Django documentation.
        """
        import datahub.omis.notification.signal_receivers  # noqa: F401
