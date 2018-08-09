from django.db.models.signals import post_save

from ..models import RelatedModel as DBRelatedModel, SimpleModel as DBSimpleModel
from ....signals import SignalReceiver


def _dummy_callback(sender, instance, **kwargs):
    """
    Function called post-save and deliberately empty.
    It can be used to check if/when it's called.
    """


def dummy_callback(*args, **kwargs):
    """
    Forward calls to _dummy_callback.

    This is so that tests can patch _dummy_callback to check if it has been called.
    """
    _dummy_callback(*args, **kwargs)


receivers = (
    SignalReceiver(post_save, DBSimpleModel, dummy_callback),
    SignalReceiver(post_save, DBRelatedModel, dummy_callback),
)
