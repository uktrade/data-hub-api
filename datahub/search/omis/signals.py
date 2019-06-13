from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany, Contact as DBContact
from datahub.omis.order.models import (
    Order as DBOrder,
    OrderAssignee as DBOrderAssignee,
    OrderSubscriber as DBOrderSubscriber,
)
from datahub.search.omis import OrderSearchApp
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async, sync_related_objects_async


def order_sync_es(instance):
    """Sync an order to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(OrderSearchApp, instance.pk),
    )


def related_order_sync_es(instance):
    """Sync an order linked from the instance to the Elasticsearch."""
    order_sync_es(instance.order)


def sync_related_orders_to_es(instance):
    """Sync related orders."""
    transaction.on_commit(
        lambda: sync_related_objects_async(instance, 'orders'),
    )


receivers = (
    SignalReceiver(post_save, DBOrder, order_sync_es),
    SignalReceiver(post_save, DBOrderSubscriber, related_order_sync_es),
    SignalReceiver(post_delete, DBOrderSubscriber, related_order_sync_es),
    SignalReceiver(post_save, DBOrderAssignee, related_order_sync_es),
    SignalReceiver(post_delete, DBOrderAssignee, related_order_sync_es),
    SignalReceiver(post_save, DBCompany, sync_related_orders_to_es),
    SignalReceiver(post_save, DBContact, sync_related_orders_to_es),
)
