from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany
from datahub.investment.investor_profile.constants import ProfileType
from datahub.investment.investor_profile.models import InvestorProfile as DBInvestorProfile
from datahub.search.deletion import delete_document
from datahub.search.large_investor_profile import LargeInvestorProfileSearchApp
from datahub.search.large_investor_profile.models import (
    LargeInvestorProfile as ESLargeInvestorProfile,
)
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async, sync_related_objects_async


def investor_profile_sync_es(instance):
    """Sync investor profile to Elasticsearch."""
    if instance.profile_type_id == ProfileType.large.value.id:
        transaction.on_commit(
            lambda: sync_object_async(LargeInvestorProfileSearchApp, instance.pk),
        )


def related_investor_profiles_sync_es(instance):
    """Sync related Company investor profiles to Elasticsearch."""
    transaction.on_commit(
        lambda: sync_related_objects_async(
            instance,
            'investor_profiles',
            related_obj_filter={'profile_type_id': ProfileType.large.value.id},
        ),
    )


def remove_investor_profile_from_es(instance):
    """Remove investor profile from es."""
    if instance.profile_type_id == ProfileType.large.value.id:
        transaction.on_commit(
            lambda pk=instance.pk: delete_document(ESLargeInvestorProfile, pk),
        )


receivers = (
    SignalReceiver(post_save, DBInvestorProfile, investor_profile_sync_es),
    SignalReceiver(post_save, DBCompany, related_investor_profiles_sync_es),
    SignalReceiver(post_delete, DBInvestorProfile, remove_investor_profile_from_es),
)
