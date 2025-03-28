from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany
from datahub.interaction.models import Interaction as DBInteraction
from datahub.search.company import CompanySearchApp
from datahub.search.company.models import (
    Company as SearchCompany,
)
from datahub.search.deletion import delete_document
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async, sync_related_objects_async


def company_sync_search(instance):
    """Sync company to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(CompanySearchApp, instance.pk),
    )


def company_subsidiaries_sync_search(instance):
    """Sync company subsidiaries to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_related_objects_async(instance, 'subsidiaries'),
    )


def company_investment_projects_sync_search(instance):
    """Sync investment projects to OpenSearch."""
    transaction.on_commit(
        lambda: sync_related_objects_async(instance, 'investor_investment_projects'),
    )


def sync_related_company_to_opensearch(instance):
    """Sync related company."""
    transaction.on_commit(
        lambda: sync_object_async(CompanySearchApp, instance.company.pk),
    )


def remove_company_from_opensearch(instance):
    """Remove company from opensearch."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(SearchCompany, pk),
    )


receivers = (
    SignalReceiver(post_save, DBCompany, company_sync_search),
    SignalReceiver(post_save, DBCompany, company_subsidiaries_sync_search),
    SignalReceiver(post_save, DBCompany, company_investment_projects_sync_search),
    SignalReceiver(post_save, DBInteraction, sync_related_company_to_opensearch),
    SignalReceiver(post_delete, DBCompany, remove_company_from_opensearch),
)
