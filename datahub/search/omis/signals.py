from django.db import transaction
from django.db.models.signals import post_save

from datahub.omis.order.models import Order as DBOrder

from .models import Order as ESOrder
from ..signals import sync_es


def order_sync_es(sender, instance, **kwargs):
    """Sync an order to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(ESOrder, DBOrder, str(instance.pk))
    )


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(
        order_sync_es,
        sender=DBOrder,
        dispatch_uid='order_sync_es'
    )


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(
        order_sync_es,
        sender=DBOrder,
        dispatch_uid='order_sync_es'
    )
