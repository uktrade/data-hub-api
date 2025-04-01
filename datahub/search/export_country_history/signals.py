from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import CompanyExportCountryHistory as DBCompanyExportCountryHistory
from datahub.search.deletion import delete_document
from datahub.search.export_country_history import ExportCountryHistoryApp
from datahub.search.export_country_history.models import (
    ExportCountryHistory as SearchExportCountryHistory,
)
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async


def export_country_history_sync_search(instance):
    """Sync export country history to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(ExportCountryHistoryApp, instance.pk),
    )


def remove_export_country_history_from_opensearch(instance):
    """Remove export country history from opensearch."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(SearchExportCountryHistory, pk),
    )


receivers = (
    SignalReceiver(post_save, DBCompanyExportCountryHistory, export_country_history_sync_search),
    SignalReceiver(
        post_delete,
        DBCompanyExportCountryHistory,
        remove_export_country_history_from_opensearch,
    ),
)
