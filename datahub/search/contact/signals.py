from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import Company as DBCompany, Contact as DBContact
from datahub.search.contact.models import Contact as ESContact
from datahub.search.signals import SignalReceiver
from datahub.search.sync_async import sync_object_async


def contact_sync_es(sender, instance, **kwargs):
    """Sync contact to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(ESContact, DBContact, str(instance.pk)),
    )


def related_contact_sync_es(sender, instance, **kwargs):
    """Sync related Company Contacts."""
    for contact in instance.contacts.all():
        contact_sync_es(sender, contact, **kwargs)


receivers = (
    SignalReceiver(post_save, DBContact, contact_sync_es),
    SignalReceiver(post_save, DBCompany, related_contact_sync_es),
)
