from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany
from datahub.investment.opportunity.models import (
    LargeCapitalOpportunity as DBLargeCapitalOpportunity,
)
from datahub.search.deletion import delete_document
from datahub.search.large_capital_opportunity import LargeCapitalOpportunitySearchApp
from datahub.search.large_capital_opportunity.models import (
    LargeCapitalOpportunity as ESLargeCapitalOpportunity,
)
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async, sync_related_objects_async


def large_capital_opportunity_sync_es(instance):
    """Sync large capital opportunity to Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(LargeCapitalOpportunitySearchApp, instance.pk),
    )


def related_large_capital_opportunity_sync_es(instance):
    """Sync related large capital opportunity Promoters to Elasticsearch."""
    transaction.on_commit(
        lambda: sync_related_objects_async(
            instance,
            'opportunities',
        ),
    )


def remove_large_capital_opportunity_from_es(instance):
    """Remove large capital opportunity from es."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(ESLargeCapitalOpportunity, pk),
    )


receivers = (
    SignalReceiver(post_save, DBLargeCapitalOpportunity, large_capital_opportunity_sync_es),
    SignalReceiver(post_save, DBCompany, related_large_capital_opportunity_sync_es),
    SignalReceiver(
        post_delete,
        DBLargeCapitalOpportunity,
        remove_large_capital_opportunity_from_es,
    ),
)
