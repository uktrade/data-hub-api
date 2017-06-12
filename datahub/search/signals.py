from django.db.models.signals import post_save
from django.dispatch import receiver

from datahub.company.models import Company as DBCompany, Contact as DBContact
from datahub.search import elasticsearch
from datahub.search.models import Company, Contact


@receiver(post_save, sender=DBCompany, dispatch_uid='company_sync_es')
def company_sync_es(sender, instance, **kwargs):
    """Sync company to the Elasticsearch."""
    doc = Company.es_document(instance)
    elasticsearch.bulk(actions=(doc,), chunk_size=1)


@receiver(post_save, sender=DBContact, dispatch_uid='contact_sync_es')
def contact_sync_es(sender, instance, **kwargs):
    """Sync contact to the Elasticsearch."""
    doc = Contact.es_document(instance)
    elasticsearch.bulk(actions=(doc,), chunk_size=1)
