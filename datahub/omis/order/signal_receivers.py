from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from datahub.omis.order.models import Order, OrderAssignee
from datahub.omis.order.pricing import update_order_pricing


@receiver(pre_save, sender=Order)
def update_order_pricing_on_pre_order_save(sender, instance, **kwargs):
    """
    Update the order pricing before an order is saved.
    Do not commit as the actual commit will be performed later on by the action triggerer.
    """
    update_order_pricing(instance, commit=False)


@receiver(post_save, sender=OrderAssignee)
def update_order_pricing_on_related_obj_save(sender, instance, **kwargs):
    """
    Update the order pricing after an order assignee is saved or deleted.
    """
    update_order_pricing(instance.order, commit=True)


@receiver(post_delete, sender=OrderAssignee)
def update_order_pricing_if_assignee_removed(sender, instance, **kwargs):
    """
    Update the order pricing after an order assignee is deleted.

    If the deletion comes from the Order, that means the Order has been
    deleted so don't save the Order again.
    """
    # If we hit the post_delete signal for `OrderAssignee` by deleting
    # an Order, do nothing as the Order is being deleted.
    origin = kwargs.get('origin')
    if origin and origin == instance.order:
        return

    update_order_pricing(instance.order, commit=True)
