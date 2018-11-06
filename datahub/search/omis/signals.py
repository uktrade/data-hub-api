from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.omis.order.models import (
    Order as DBOrder,
    OrderAssignee as DBOrderAssignee,
    OrderSubscriber as DBOrderSubscriber,
)
from datahub.search.omis import OrderSearchApp
from datahub.search.signals import SignalReceiver
from datahub.search.sync_async import sync_object_async


def order_sync_es(instance):
    """Sync an order to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(OrderSearchApp, str(instance.pk)),
    )


def related_order_sync_es(instance):
    """Sync an order linked from the instance to the Elasticsearch."""
    order_sync_es(instance.order)


receivers = (
    SignalReceiver(post_save, DBOrder, order_sync_es),
    SignalReceiver(post_save, DBOrderSubscriber, related_order_sync_es),
    SignalReceiver(post_delete, DBOrderSubscriber, related_order_sync_es),
    SignalReceiver(post_save, DBOrderAssignee, related_order_sync_es),
    SignalReceiver(post_delete, DBOrderAssignee, related_order_sync_es),
)
