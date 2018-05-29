from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class AdminReportConfig(AppConfig):
    """App config for the admin_report app."""

    name = 'datahub.admin_report'

    def ready(self):
        """Auto-discovers admin_report modules in loaded apps."""
        autodiscover_modules('admin_reports')
