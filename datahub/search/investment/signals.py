from django.db import transaction
from django.db.models.query_utils import Q
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Advisor
from datahub.investment.models import (
    InvestmentProject as DBInvestmentProject,
    InvestmentProjectTeamMember,
)
from .models import InvestmentProject as ESInvestmentProject
from ..signals import SignalReceiver
from ..sync_async import sync_object_async


def investment_project_sync_es(sender, instance, **kwargs):
    """Sync investment project to the Elasticsearch."""
    def sync_es_wrapper():
        if isinstance(instance, InvestmentProjectTeamMember):
            pk = instance.investment_project.pk
        else:
            pk = instance.pk

        sync_object_async(
            ESInvestmentProject,
            DBInvestmentProject,
            str(pk),
        )

    transaction.on_commit(sync_es_wrapper)


def investment_project_sync_es_adviser_change(sender, instance, **kwargs):
    """
    post_save handler for advisers, to make sure that any projects they're linked to are
    resynced.

    This is primarily to update the teams stored against the project in ES.
    """
    def sync_es_wrapper():
        queryset = DBInvestmentProject.objects.filter(
            Q(created_by_id=instance.pk)
            | Q(client_relationship_manager_id=instance.pk)
            | Q(project_manager_id=instance.pk)
            | Q(project_assurance_adviser_id=instance.pk)
            | Q(team_members__adviser_id=instance.pk),
        )

        for project in queryset:
            sync_object_async(
                ESInvestmentProject,
                DBInvestmentProject,
                str(project.pk),
            )

    transaction.on_commit(sync_es_wrapper)


receivers = (
    SignalReceiver(post_save, DBInvestmentProject, investment_project_sync_es),
    SignalReceiver(post_save, InvestmentProjectTeamMember, investment_project_sync_es),
    SignalReceiver(post_delete, InvestmentProjectTeamMember, investment_project_sync_es),
    SignalReceiver(post_save, Advisor, investment_project_sync_es_adviser_change),
)
