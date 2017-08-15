from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import Contact as DBContact

from .models import Contact as ESContact
from ..signals import sync_es


def contact_sync_es(sender, instance, **kwargs):
    """Sync contact to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(ESContact, DBContact, str(instance.pk))
    )


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(contact_sync_es, sender=DBContact, dispatch_uid='contact_sync_es')


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(contact_sync_es, sender=DBContact, dispatch_uid='contact_sync_es')
