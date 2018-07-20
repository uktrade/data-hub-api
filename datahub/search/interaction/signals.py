from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany, Contact as DBContact
from datahub.interaction.models import Interaction as DBInteraction
from datahub.investment.models import InvestmentProject as DBInvestmentProject
from datahub.search.query_builder import delete_document
from datahub.search.signals import SignalReceiver
from datahub.search.sync_async import sync_object_async
from .models import Interaction as ESInteraction


def sync_interaction_to_es(sender, instance, **kwargs):
    """Sync interaction to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(ESInteraction, DBInteraction, str(instance.pk))
    )


def remove_interaction_from_es(sender, instance, **kwargs):
    """Remove interaction from es."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(ESInteraction, str(pk))
    )


def sync_related_interactions_to_es(sender, instance, **kwargs):
    """Sync related interactions."""
    for contact in instance.interactions.all():
        sync_interaction_to_es(sender, contact, **kwargs)


receivers = (
    SignalReceiver(post_save, DBInteraction, sync_interaction_to_es),
    SignalReceiver(post_save, DBCompany, sync_related_interactions_to_es),
    SignalReceiver(post_save, DBContact, sync_related_interactions_to_es),
    SignalReceiver(post_save, DBInvestmentProject, sync_related_interactions_to_es),
    SignalReceiver(post_delete, DBInteraction, remove_interaction_from_es),
)
