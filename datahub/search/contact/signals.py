from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from datahub.company.models import Contact as DBContact
from datahub.core.utils import executor

from .models import Contact as ESContact
from ..signals import sync_es


@receiver(post_save, sender=DBContact, dispatch_uid='contact_sync_es')
def contact_sync_es(sender, instance, **kwargs):
    """Sync contact to the Elasticsearch."""
    transaction.on_commit(
        lambda: executor.submit(sync_es, ESContact, DBContact, str(instance.pk))
    )
