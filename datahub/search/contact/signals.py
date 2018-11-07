from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import Company as DBCompany, Contact as DBContact
from datahub.search.contact import ContactSearchApp
from datahub.search.signals import SignalReceiver
from datahub.search.sync_async import sync_object_async


def contact_sync_es(instance):
    """Sync contact to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(ContactSearchApp, instance.pk),
    )


def related_contact_sync_es(instance):
    """Sync related Company Contacts."""
    for contact in instance.contacts.all():
        contact_sync_es(contact)


receivers = (
    SignalReceiver(post_save, DBContact, contact_sync_es),
    SignalReceiver(post_save, DBCompany, related_contact_sync_es),
)
