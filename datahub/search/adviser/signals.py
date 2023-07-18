from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import Advisor as DBAdviser
from datahub.search.adviser import AdviserSearchApp
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async


def sync_event_to_opensearch(instance):
    """Sync event to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(AdviserSearchApp, instance.pk),
    )


receivers = (SignalReceiver(post_save, DBAdviser, sync_event_to_opensearch),)
