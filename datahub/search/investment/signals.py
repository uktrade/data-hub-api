from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from datahub.core.utils import executor
from datahub.investment.models import InvestmentProject as DBInvestmentProject

from .models import InvestmentProject as ESInvestmentProject
from ..signals import sync_es


@receiver(post_save, sender=DBInvestmentProject, dispatch_uid='investment_project_sync_es')
def investment_project_sync_es(sender, instance, **kwargs):
    """Sync investment project to the Elasticsearch."""
    transaction.on_commit(
        lambda: executor.submit(
            sync_es,
            ESInvestmentProject,
            DBInvestmentProject,
            str(instance.pk),
        )
    )
