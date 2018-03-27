from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import Company as DBCompany, Contact as DBContact
from .models import Contact as ESContact
from ..signals import SignalReceiver, sync_es


def contact_sync_es(sender, instance, **kwargs):
    """Sync contact to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(ESContact, DBContact, str(instance.pk))
    )


def related_contact_sync_es(sender, instance, **kwargs):
    """Sync related Company Contacts."""
    for contact in instance.contacts.all():
        contact_sync_es(sender, contact, **kwargs)


receivers = (
    SignalReceiver(post_save, DBContact, contact_sync_es),
    SignalReceiver(post_save, DBCompany, related_contact_sync_es),
)
