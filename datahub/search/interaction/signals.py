from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany, Contact as DBContact
from datahub.interaction.models import Interaction as DBInteraction
from datahub.investment.models import InvestmentProject as DBInvestmentProject
from datahub.search.elasticsearch import delete_document
from datahub.search.signals import sync_es
from .models import Interaction as ESInteraction


def sync_interaction_to_es(sender, instance, **kwargs):
    """Sync interaction to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(ESInteraction, DBInteraction, str(instance.pk))
    )


def remove_interaction_from_es(sender, instance, **kwargs):
    """Remove interaction from es."""
    transaction.on_commit(
        lambda: delete_document(ESInteraction, str(instance.pk))
    )


def sync_related_interactions_to_es(sender, instance, **kwargs):
    """Sync related interactions."""
    for contact in instance.interactions.all():
        sync_interaction_to_es(sender, contact, **kwargs)


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(
        sync_interaction_to_es,
        sender=DBInteraction,
        dispatch_uid='sync_interaction_to_es'
    )

    post_save.connect(
        sync_related_interactions_to_es,
        sender=DBCompany,
        dispatch_uid='company_sync_related_interactions_to_es'
    )

    post_save.connect(
        sync_related_interactions_to_es,
        sender=DBContact,
        dispatch_uid='contact_sync_related_interactions_to_es'
    )

    post_save.connect(
        sync_related_interactions_to_es,
        sender=DBInvestmentProject,
        dispatch_uid='iproject_sync_related_interactions_to_es'
    )

    post_delete.connect(
        remove_interaction_from_es,
        sender=DBInteraction,
        dispatch_uid='remove_interaction_from_es',
    )


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(
        sync_interaction_to_es,
        sender=DBInteraction,
        dispatch_uid='sync_interaction_to_es'
    )

    post_save.disconnect(
        sync_related_interactions_to_es,
        sender=DBCompany,
        dispatch_uid='company_sync_related_interactions_to_es'
    )

    post_save.disconnect(
        sync_related_interactions_to_es,
        sender=DBContact,
        dispatch_uid='contact_sync_related_interactions_to_es'
    )

    post_save.disconnect(
        sync_related_interactions_to_es,
        sender=DBInvestmentProject,
        dispatch_uid='iproject_sync_related_interactions_to_es'
    )
