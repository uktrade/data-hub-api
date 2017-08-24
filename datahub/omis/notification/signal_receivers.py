from django.db.models.signals import post_save
from django.dispatch import receiver

from datahub.omis.notification.client import notify
from datahub.omis.order.models import Order


@receiver(post_save, sender=Order, dispatch_uid='notify_post_save_order')
def notify_post_save_order(sender, instance, created, **kwargs):
    """Notify people that a new order has been created."""
    if created:
        notify.order_created(instance)
