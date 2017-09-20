from django.apps import AppConfig


class OrderConfig(AppConfig):
    """
    Django App Config for the Order app.
    """

    name = 'datahub.omis.order'

    def ready(self):
        """Registers the signals for this app.

        This is the preferred way to register signals in the Django documentation.
        """
        import datahub.omis.order.signal_receivers  # noqa: F401
