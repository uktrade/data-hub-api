from django.db import transaction
from django.db.models.signals import post_save

from datahub.event.models import Event as DBEvent
from datahub.search.signals import sync_es
from .models import Event as ESEvent


def sync_event_to_es(sender, instance, **kwargs):
    """Sync event to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(ESEvent, DBEvent, str(instance.pk))
    )


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(
        sync_event_to_es,
        sender=DBEvent,
        dispatch_uid='sync_event_to_es'
    )


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(
        sync_event_to_es,
        sender=DBEvent,
        dispatch_uid='sync_event_to_es'
    )
