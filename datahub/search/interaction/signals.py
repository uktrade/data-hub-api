from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany
from datahub.company.models import Contact as DBContact
from datahub.interaction.models import (
    Interaction as DBInteraction,
)
from datahub.interaction.models import (
    InteractionDITParticipant as DBInteractionDITParticipant,
)
from datahub.investment.project.models import InvestmentProject as DBInvestmentProject
from datahub.search.deletion import delete_document
from datahub.search.interaction import InteractionSearchApp
from datahub.search.interaction.models import Interaction as SearchInteraction
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async, sync_related_objects_async


def sync_interaction_to_opensearch(instance):
    """Sync interaction to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(InteractionSearchApp, instance.pk),
    )


def sync_participant_to_opensearch(dit_participant):
    """Sync a DIT participant's interaction to OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(InteractionSearchApp, dit_participant.interaction_id),
    )


def remove_interaction_from_opensearch(instance):
    """Remove interaction from es."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(SearchInteraction, pk),
    )


def sync_related_interactions_to_opensearch(instance):
    """Sync related interactions."""
    transaction.on_commit(
        lambda: sync_related_objects_async(instance, 'interactions', None, 'interaction'),
    )


receivers = (
    SignalReceiver(post_save, DBInteraction, sync_interaction_to_opensearch),
    SignalReceiver(post_save, DBInteractionDITParticipant, sync_participant_to_opensearch),
    SignalReceiver(post_save, DBCompany, sync_related_interactions_to_opensearch),
    SignalReceiver(post_save, DBContact, sync_related_interactions_to_opensearch),
    SignalReceiver(post_save, DBInvestmentProject, sync_related_interactions_to_opensearch),
    SignalReceiver(post_delete, DBInteraction, remove_interaction_from_opensearch),
)
