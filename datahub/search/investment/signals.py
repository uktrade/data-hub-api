from django.db import transaction
from django.db.models.signals import post_save

from datahub.investment.models import InvestmentProject as DBInvestmentProject

from .models import InvestmentProject as ESInvestmentProject
from ..signals import sync_es


def investment_project_sync_es(sender, instance, **kwargs):
    """Sync investment project to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(
            ESInvestmentProject,
            DBInvestmentProject,
            str(instance.pk),
        )
    )


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(
        investment_project_sync_es,
        sender=DBInvestmentProject,
        dispatch_uid='investment_project_sync_es'
    )


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(
        investment_project_sync_es,
        sender=DBInvestmentProject,
        dispatch_uid='investment_project_sync_es'
    )
