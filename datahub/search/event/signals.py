from django.db import transaction
from django.db.models.signals import post_save

from datahub.event.models import Event as DBEvent
from datahub.search.event import EventSearchApp
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async


def sync_event_to_es(instance):
    """Sync event to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(EventSearchApp, instance.pk),
    )


receivers = (SignalReceiver(post_save, DBEvent, sync_event_to_es),)
