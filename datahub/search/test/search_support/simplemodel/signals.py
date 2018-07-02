from django.db.models.signals import post_delete, pre_delete

from ..models import SimpleModel as DBSimpleModel
from ....signals import SignalReceiver


def dummy_on_delete_callback(sender, instance, **kwargs):
    """
    Function called on_delete and deliberately empty.
    It can be used to check if/when it's called.
    """


receivers = (
    SignalReceiver(post_delete, DBSimpleModel, dummy_on_delete_callback),
    SignalReceiver(pre_delete, DBSimpleModel, dummy_on_delete_callback),
)
