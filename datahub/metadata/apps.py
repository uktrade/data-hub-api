from django.apps import AppConfig


class MetadataConfig(AppConfig):
    """
    Django App Config for the Metadata app.
    """

    name = 'datahub.metadata'

    def ready(self):
        """Calls the autodiscover logic after all apps are loaded."""
        super().ready()
        self.module.autodiscover()
