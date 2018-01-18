from django.apps import AppConfig


class CompanyConfig(AppConfig):
    """Configuration class for this app."""

    name = 'datahub.company'

    def ready(self):
        """Registers the signal receivers for this app.

        This is the preferred way to register signal receivers in the Django documentation.
        """
        import datahub.company.signals  # noqa: F401
