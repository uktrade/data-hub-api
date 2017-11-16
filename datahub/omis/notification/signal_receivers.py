from django.db.models.signals import post_save
from django.dispatch import receiver

from datahub.omis.notification.client import notify
from datahub.omis.order.models import Order, OrderAssignee, OrderSubscriber
from datahub.omis.order.signals import (
    order_cancelled, order_completed, order_paid,
    quote_accepted, quote_generated
)


@receiver(post_save, sender=Order, dispatch_uid='notify_post_save_order')
def notify_post_save_order(sender, instance, created, raw=False, **kwargs):
    """Notify people that a new order has been created."""
    if raw:  # e.g. when loading fixtures
        return

    if created:
        notify.order_created(instance)


@receiver(post_save, sender=OrderAssignee, dispatch_uid='notify_post_save_assignee')
@receiver(post_save, sender=OrderSubscriber, dispatch_uid='notify_post_save_subscriber')
def notify_post_save_order_adviser(sender, instance, created, raw=False, **kwargs):
    """Notify people that they have been added to the order"""
    if raw:  # e.g. when loading fixtures
        return

    if created:
        notify.adviser_added(
            order=instance.order,
            adviser=instance.adviser,
            by=instance.created_by,
            creation_date=instance.created_on
        )


@receiver(order_paid, sender=Order, dispatch_uid='notify_post_order_paid')
def notify_post_order_paid(sender, order, **kwargs):
    """Notify people that an order has been marked as paid."""
    notify.order_paid(order)


@receiver(order_completed, sender=Order, dispatch_uid='notify_post_order_completed')
def notify_post_order_completed(sender, order, **kwargs):
    """Notify people that an order has been marked as completed."""
    notify.order_completed(order)


@receiver(order_cancelled, sender=Order, dispatch_uid='notify_post_order_cancelled')
def notify_post_order_cancelled(sender, order, **kwargs):
    """Notify people that an order has been cancelled."""
    notify.order_cancelled(order)


@receiver(quote_generated, sender=Order, dispatch_uid='notify_post_quote_generated')
def notify_post_quote_generated(sender, order, **kwargs):
    """Notify people that a quote has been generated."""
    notify.quote_generated(order)


@receiver(quote_accepted, sender=Order, dispatch_uid='notify_post_quote_accepted')
def notify_post_quote_accepted(sender, order, **kwargs):
    """Notify people that a quote has been accepted."""
    notify.quote_accepted(order)
