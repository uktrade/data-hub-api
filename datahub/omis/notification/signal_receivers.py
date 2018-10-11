from functools import partial

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from datahub.omis.notification.client import notify
from datahub.omis.order.models import Order, OrderAssignee, OrderSubscriber
from datahub.omis.order.signals import (
    order_cancelled,
    order_completed,
    order_paid,
    quote_accepted,
    quote_cancelled,
    quote_generated,
)


@receiver(post_save, sender=Order, dispatch_uid='notify_post_save_order')
def notify_post_save_order(sender, instance, created, raw=False, **kwargs):
    """Notify people that a new order has been created."""
    if raw:  # e.g. when loading fixtures
        return

    if created:
        transaction.on_commit(partial(notify.order_created, instance))


@receiver(post_save, sender=OrderAssignee, dispatch_uid='notify_post_save_assignee')
@receiver(post_save, sender=OrderSubscriber, dispatch_uid='notify_post_save_subscriber')
def notify_post_save_order_adviser(sender, instance, created, raw=False, **kwargs):
    """Notify people that they have been added to the order"""
    if raw:  # e.g. when loading fixtures
        return

    if created:
        transaction.on_commit(
            partial(
                notify.adviser_added,
                order=instance.order,
                adviser=instance.adviser,
                by=instance.created_by,
                creation_date=instance.created_on,
            ),
        )


@receiver(post_delete, sender=OrderAssignee, dispatch_uid='notify_post_delete_assignee')
@receiver(post_delete, sender=OrderSubscriber, dispatch_uid='notify_post_delete_subscriber')
def notify_post_delete_order_adviser(sender, instance, **kwargs):
    """
    Notify people that they have been removed from the order.

    Note that `instance` is no longer in the database at this point,
    so be very careful what you do with it.
    """
    transaction.on_commit(
        partial(notify.adviser_removed, order=instance.order, adviser=instance.adviser),
    )


@receiver(order_paid, sender=Order, dispatch_uid='notify_post_order_paid')
def notify_post_order_paid(sender, order, **kwargs):
    """Notify people that an order has been marked as paid."""
    transaction.on_commit(partial(notify.order_paid, order))


@receiver(order_completed, sender=Order, dispatch_uid='notify_post_order_completed')
def notify_post_order_completed(sender, order, **kwargs):
    """Notify people that an order has been marked as completed."""
    transaction.on_commit(partial(notify.order_completed, order))


@receiver(order_cancelled, sender=Order, dispatch_uid='notify_post_order_cancelled')
def notify_post_order_cancelled(sender, order, **kwargs):
    """Notify people that an order has been cancelled."""
    transaction.on_commit(partial(notify.order_cancelled, order))


@receiver(quote_generated, sender=Order, dispatch_uid='notify_post_quote_generated')
def notify_post_quote_generated(sender, order, **kwargs):
    """Notify people that a quote has been generated."""
    transaction.on_commit(partial(notify.quote_generated, order))


@receiver(quote_accepted, sender=Order, dispatch_uid='notify_post_quote_accepted')
def notify_post_quote_accepted(sender, order, **kwargs):
    """Notify people that a quote has been accepted."""
    transaction.on_commit(partial(notify.quote_accepted, order))


@receiver(quote_cancelled, sender=Order, dispatch_uid='notify_post_quote_cancelled')
def notify_post_quote_cancelled(sender, order, by, **kwargs):
    """Notify people that a quote has been cancelled."""
    transaction.on_commit(partial(notify.quote_cancelled, order, by))
