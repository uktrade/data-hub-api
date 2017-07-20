from django.apps import AppConfig


class InvestmentConfig(AppConfig):
    """Configuration class for this app."""

    name = 'datahub.investment'

    def ready(self):
        """Registers the signals for this app.

        This is the preferred way to register signals in the Django documentation.
        """
        import datahub.investment.signals  # noqa: F401
