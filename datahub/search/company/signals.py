from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import Company as DBCompany
from datahub.interaction.models import Interaction as DBInteraction
from datahub.search.company import CompanySearchApp
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async, sync_related_objects_async


def company_sync_es(instance):
    """Sync company to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(CompanySearchApp, instance.pk),
    )


def company_subsidiaries_sync_es(instance):
    """Sync company subsidiaries to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_related_objects_async(instance, 'subsidiaries'),
    )


def sync_related_company_to_es(instance):
    """Sync related company."""
    transaction.on_commit(
        lambda: sync_object_async(CompanySearchApp, instance.company.pk),
    )


receivers = (
    SignalReceiver(post_save, DBCompany, company_sync_es),
    SignalReceiver(post_save, DBCompany, company_subsidiaries_sync_es),
    SignalReceiver(post_save, DBInteraction, sync_related_company_to_es),
)
