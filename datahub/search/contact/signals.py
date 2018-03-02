from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import Company as DBCompany, Contact as DBContact
from .models import Contact as ESContact
from ..signals import sync_es


def contact_sync_es(sender, instance, **kwargs):
    """Sync contact to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(ESContact, DBContact, str(instance.pk))
    )


def related_contact_sync_es(sender, instance, **kwargs):
    """Sync related Company Contacts."""
    for contact in instance.contacts.all():
        contact_sync_es(sender, contact, **kwargs)


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(
        contact_sync_es,
        sender=DBContact,
        dispatch_uid='contact_sync_es'
    )

    post_save.connect(
        related_contact_sync_es,
        sender=DBCompany,
        dispatch_uid='related_contact_sync_es'
    )


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(
        contact_sync_es,
        sender=DBContact,
        dispatch_uid='contact_sync_es'
    )

    post_save.disconnect(
        related_contact_sync_es,
        sender=DBCompany,
        dispatch_uid='related_contact_sync_es'
    )
