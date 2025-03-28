from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.event.models import Event as DBEvent
from datahub.search.deletion import delete_document
from datahub.search.event import EventSearchApp
from datahub.search.event.models import (
    Event as SearchEvent,
)
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async


def sync_event_to_opensearch(instance):
    """Sync event to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(EventSearchApp, instance.pk),
    )


def remove_event_from_opensearch(instance):
    """Remove event from opensearch."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(SearchEvent, pk),
    )


receivers = (
    SignalReceiver(post_save, DBEvent, sync_event_to_opensearch),
    SignalReceiver(post_delete, DBEvent, remove_event_from_opensearch),
)
