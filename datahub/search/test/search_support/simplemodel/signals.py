from django.db.models.signals import post_delete, pre_delete

from datahub.search.signals import SignalReceiver
from datahub.search.test.search_support.models import SimpleModel as DBSimpleModel


def dummy_on_delete_callback(instance):
    """
    Function called on_delete and deliberately empty.
    It can be used to check if/when it's called.
    """


receivers = (
    SignalReceiver(post_delete, DBSimpleModel, dummy_on_delete_callback),
    SignalReceiver(pre_delete, DBSimpleModel, dummy_on_delete_callback),
)
