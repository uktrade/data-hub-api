from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Advisor as DBAdviser
from datahub.search.adviser import AdviserSearchApp
from datahub.search.adviser.models import (
    Adviser as SearchAdviser,
)
from datahub.search.deletion import delete_document
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async


def sync_adviser_to_opensearch(instance):
    """Sync adviser to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(AdviserSearchApp, instance.pk),
    )


def remove_adviser_from_opensearch(instance):
    """Remove adviser from opensearch."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(SearchAdviser, pk),
    )


receivers = (
    SignalReceiver(post_save, DBAdviser, sync_adviser_to_opensearch),
    SignalReceiver(post_delete, DBAdviser, remove_adviser_from_opensearch),
)
