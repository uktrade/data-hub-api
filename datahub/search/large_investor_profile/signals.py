from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany
from datahub.investment.investor_profile.models import (
    LargeCapitalInvestorProfile as DBLargeCapitalInvestorProfile,
)
from datahub.search.deletion import delete_document
from datahub.search.large_investor_profile import LargeInvestorProfileSearchApp
from datahub.search.large_investor_profile.models import (
    LargeInvestorProfile as SearchLargeInvestorProfile,
)
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async, sync_related_objects_async


def investor_profile_sync_search(instance):
    """Sync investor profile to OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(LargeInvestorProfileSearchApp, instance.pk),
    )


def related_investor_profiles_sync_search(instance):
    """Sync related Company investor profiles to OpenSearch."""
    transaction.on_commit(
        lambda: sync_related_objects_async(
            instance,
            'investor_profiles',
        ),
    )


def remove_investor_profile_from_opensearch(instance):
    """Remove investor profile from es."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(SearchLargeInvestorProfile, pk),
    )


receivers = (
    SignalReceiver(post_save, DBLargeCapitalInvestorProfile, investor_profile_sync_search),
    SignalReceiver(post_save, DBCompany, related_investor_profiles_sync_search),
    SignalReceiver(
        post_delete,
        DBLargeCapitalInvestorProfile,
        remove_investor_profile_from_opensearch,
    ),
)
