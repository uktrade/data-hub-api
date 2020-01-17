from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import CompanyExportCountryHistory as DBCompanyExportCountryHistory
from datahub.search.exportcountryhistory import ExportCountryHistoryApp
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async


def export_country_history_sync_es(instance):
    """Sync export country history to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(ExportCountryHistoryApp, instance.pk),
    )


receivers = (
    SignalReceiver(post_save, DBCompanyExportCountryHistory, export_country_history_sync_es),
)
