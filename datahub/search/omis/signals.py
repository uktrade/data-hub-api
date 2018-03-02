from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.omis.order.models import (
    Order as DBOrder,
    OrderAssignee as DBOrderAssignee,
    OrderSubscriber as DBOrderSubscriber
)
from .models import Order as ESOrder
from ..signals import sync_es


def order_sync_es(sender, instance, **kwargs):
    """Sync an order to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(ESOrder, DBOrder, str(instance.pk))
    )


def related_order_sync_es(sender, instance, **kwargs):
    """Sync an order linked from the instance to the Elasticsearch."""
    order_sync_es(sender, instance.order, **kwargs)


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(
        order_sync_es,
        sender=DBOrder,
        dispatch_uid='order_sync_es'
    )

    post_save.connect(
        related_order_sync_es,
        sender=DBOrderSubscriber,
        dispatch_uid='subscriber_added_order_sync_es'
    )
    post_delete.connect(
        related_order_sync_es,
        sender=DBOrderSubscriber,
        dispatch_uid='subscriber_deleted_order_sync_es'
    )

    post_save.connect(
        related_order_sync_es,
        sender=DBOrderAssignee,
        dispatch_uid='assignee_added_order_sync_es'
    )
    post_delete.connect(
        related_order_sync_es,
        sender=DBOrderAssignee,
        dispatch_uid='assignee_deleted_order_sync_es'
    )


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(
        sender=DBOrder,
        dispatch_uid='order_sync_es'
    )

    post_save.disconnect(
        sender=DBOrderSubscriber,
        dispatch_uid='subscriber_added_order_sync_es'
    )
    post_delete.disconnect(
        sender=DBOrderSubscriber,
        dispatch_uid='subscriber_deleted_order_sync_es'
    )

    post_save.disconnect(
        sender=DBOrderAssignee,
        dispatch_uid='assignee_added_order_sync_es'
    )
    post_delete.disconnect(
        sender=DBOrderAssignee,
        dispatch_uid='assignee_deleted_order_sync_es'
    )
