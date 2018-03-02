from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import Company as DBCompany
from .models import Company as ESCompany
from ..signals import sync_es


def company_sync_es(sender, instance, **kwargs):
    """Sync company to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(ESCompany, DBCompany, str(instance.pk))
    )


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(company_sync_es, sender=DBCompany, dispatch_uid='company_sync_es')


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(company_sync_es, sender=DBCompany, dispatch_uid='company_sync_es')
