from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import Company as DBCompany
from datahub.search.company import CompanySearchApp
from datahub.search.signals import SignalReceiver
from datahub.search.sync_async import sync_object_async


def company_sync_es(instance):
    """Sync company to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(CompanySearchApp, instance.pk),
    )


receivers = (SignalReceiver(post_save, DBCompany, company_sync_es),)
