from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from datahub.company.models import Company as DBCompany
from datahub.core.utils import executor

from .models import Company as ESCompany
from ..signals import sync_es


@receiver(post_save, sender=DBCompany, dispatch_uid='company_sync_es')
def company_sync_es(sender, instance, **kwargs):
    """Sync company to the Elasticsearch."""
    transaction.on_commit(
        lambda: executor.submit(sync_es, ESCompany, DBCompany, str(instance.pk))
    )
