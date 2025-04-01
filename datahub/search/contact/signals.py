from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany
from datahub.company.models import Contact as DBContact
from datahub.search.contact import ContactSearchApp
from datahub.search.contact.models import Contact as SearchContact
from datahub.search.deletion import delete_document
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async, sync_related_objects_async


def contact_sync_search(instance):
    """Sync contact to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(ContactSearchApp, instance.pk),
    )


def related_contact_sync_search(instance):
    """Sync related Company Contacts."""
    transaction.on_commit(
        lambda: sync_related_objects_async(instance, 'contacts'),
    )


def remove_contact_from_opensearch(instance):
    """Remove contact from opensearch."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(SearchContact, pk),
    )


receivers = (
    SignalReceiver(post_save, DBContact, contact_sync_search),
    SignalReceiver(post_save, DBCompany, related_contact_sync_search),
    SignalReceiver(post_delete, DBContact, remove_contact_from_opensearch),
)
