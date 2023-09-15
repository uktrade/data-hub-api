from django.apps import AppConfig


class TaskConfig(AppConfig):
    """
    Django App Config for the Task app.
    """

    name = 'datahub.task'

    def ready(self):
        """Registers the signals for this app.

        This is the preferred way to register signals in the Django documentation.
        """
        import datahub.task.signals  # noqa: F401
