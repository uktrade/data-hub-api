from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import Company as DBCompany, CompanyExportCountry
from datahub.search.company import CompanySearchApp
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async


def company_sync_es(instance):
    """Sync company to the Elasticsearch."""
    transaction.on_commit(
        lambda: sync_object_async(CompanySearchApp, instance.pk),
    )


def company_export_country_sync_es(instance):
    """Sync the company of a CompanyExportcountry to ElasticSearch"""
    transaction.on_commit(
        lambda: sync_object_async(CompanySearchApp, instance.company_id),
    )


receivers = (
    SignalReceiver(post_save, DBCompany, company_sync_es),
    SignalReceiver(post_save, CompanyExportCountry, company_export_country_sync_es),
    SignalReceiver(post_delete, CompanyExportCountry, company_export_country_sync_es),
)
