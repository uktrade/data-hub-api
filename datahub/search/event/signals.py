from django.db import transaction
from django.db.models.signals import post_save

from datahub.event.models import Event as DBEvent
from datahub.search.signals import SignalReceiver
from datahub.search.sync_async import sync_object_async
from .models import Event as ESEvent


def sync_event_to_es(sender, instance, **kwargs):
    """Sync event to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(ESEvent, DBEvent, str(instance.pk))
    )


receivers = (SignalReceiver(post_save, DBEvent, sync_event_to_es),)
