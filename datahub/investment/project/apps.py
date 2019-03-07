from django.apps import AppConfig


class InvestmentConfig(AppConfig):
    """
    Configuration class for this app.

    For legacy reasons the label of this application is investment when
    ideally it should be investment_project.
    """

    name = 'datahub.investment.project'
    label = 'investment'

    def ready(self):
        """Registers the signals for this app.

        This is the preferred way to register signals in the Django documentation.
        """
        import datahub.investment.project.signals  # noqa: F401
