from django.db.models.signals import post_save
from django.dispatch import receiver

from datahub.omis.notification.client import notify
from datahub.omis.order.models import Order
from datahub.omis.order.signals import quote_generated


@receiver(post_save, sender=Order, dispatch_uid='notify_post_save_order')
def notify_post_save_order(sender, instance, created, **kwargs):
    """Notify people that a new order has been created."""
    if created:
        notify.order_created(instance)


@receiver(quote_generated, sender=Order, dispatch_uid='notify_post_quote_generated')
def notify_post_quote_generated(sender, order, **kwargs):
    """Notify contact that a quote has been generated."""
    notify.quote_generated(order)
