from django.db.models.signals import post_save
from django.dispatch import receiver

from datahub.omis.notification.client import notify
from datahub.omis.order.models import Order, OrderAssignee, OrderSubscriber
from datahub.omis.order.signals import quote_generated


@receiver(post_save, sender=Order, dispatch_uid='notify_post_save_order')
def notify_post_save_order(sender, instance, created, raw=False, **kwargs):
    """Notify people that a new order has been created."""
    if raw:  # e.g. when loading fixtures
        return

    if created:
        notify.order_created(instance)


@receiver(quote_generated, sender=Order, dispatch_uid='notify_post_quote_generated')
def notify_post_quote_generated(sender, order, **kwargs):
    """Notify contact that a quote has been generated."""
    notify.quote_generated(order)


@receiver(post_save, sender=OrderAssignee, dispatch_uid='notify_post_save_assignee')
@receiver(post_save, sender=OrderSubscriber, dispatch_uid='notify_post_save_subscriber')
def notify_post_save_order_adviser(sender, instance, created, raw=False, **kwargs):
    """Notify adviser that they have been added to the order"""
    if raw:  # e.g. when loading fixtures
        return

    if created:
        notify.adviser_added(
            order=instance.order,
            adviser=instance.adviser,
            by=instance.created_by,
            creation_date=instance.created_on
        )
