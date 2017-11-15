from django.db import transaction
from django.db.models.signals import post_save

from datahub.investment.models import InvestmentProject as DBInvestmentProject, InvestmentProjectTeamMember

from .models import InvestmentProject as ESInvestmentProject
from ..signals import sync_es


def investment_project_sync_es(sender, instance, **kwargs):
    """Sync investment project to the Elasticsearch."""
    def sync_es_wrapper():
        if isinstance(instance, InvestmentProjectTeamMember):
            pk = instance.investment_project.pk
        elif isinstance(instance, DBInvestmentProject):
            pk = instance.pk
        else:
            return False

        sync_es(
            ESInvestmentProject,
            DBInvestmentProject,
            str(pk),
        )

    transaction.on_commit(sync_es_wrapper)


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(
        investment_project_sync_es,
        sender=DBInvestmentProject,
        dispatch_uid='investment_project_sync_es'
    )
    post_save.connect(
        investment_project_sync_es,
        sender=InvestmentProjectTeamMember,
        dispatch_uid='investment_project_sync_es'
    )


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(
        investment_project_sync_es,
        sender=DBInvestmentProject,
        dispatch_uid='investment_project_sync_es'
    )
    post_save.disconnect(
        investment_project_sync_es,
        sender=InvestmentProjectTeamMember,
        dispatch_uid='investment_project_sync_es'
    )
