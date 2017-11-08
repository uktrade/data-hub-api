from django.db import transaction
from django.db.models.signals import post_save

from datahub.company.models import CompaniesHouseCompany as DBCompaniesHouseCompany

from .models import CompaniesHouseCompany as ESCompaniesHouseCompany
from ..signals import sync_es


def companieshousecompany_sync_es(sender, instance, **kwargs):
    """Sync companies house company to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_es(
            ESCompaniesHouseCompany,
            DBCompaniesHouseCompany,
            str(instance.pk)
        )
    )


def connect_signals():
    """Connect signals for ES sync."""
    post_save.connect(
        companieshousecompany_sync_es,
        sender=DBCompaniesHouseCompany,
        dispatch_uid='companieshousecompany_sync_es'
    )


def disconnect_signals():
    """Disconnect signals from ES sync."""
    post_save.disconnect(
        companieshousecompany_sync_es,
        sender=DBCompaniesHouseCompany,
        dispatch_uid='companieshousecompany_sync_es'
    )
