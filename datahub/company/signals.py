import logging

from django.db.models.signals import post_migrate
from django.dispatch import receiver

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import (
    CompanyExportCountry,
    CompanyExportCountryHistory,
)
from datahub.company.signal_receivers import (
    export_country_delete_signal,
    export_country_update_signal,
)
from datahub.core.utils import load_constants_to_database
from datahub.metadata.models import BusinessType

logger = logging.getLogger(__name__)


@receiver(
    post_migrate,
    sender=BusinessType._meta.app_config,
    dispatch_uid='company_business_type_post_migrate',
)
def company_business_type_post_migrate(sender, **kwargs):
    """
    Ensures all business types are loaded to the database.

    Any new business types are created, and any existing ones are updated if the label has changed.
    """
    load_constants_to_database(BusinessTypeConstant, BusinessType)


@receiver(
    export_country_update_signal,
    sender=CompanyExportCountry,
    dispatch_uid='record_export_country_history_update',
)
def record_export_country_history_update(sender, instance, created, by, **kwargs):
    """
    Record export country changes to history.
    """
    action = CompanyExportCountryHistory.HistoryType.UPDATE
    if created:
        action = CompanyExportCountryHistory.HistoryType.INSERT

    _record_export_country_history(instance, action, by)


@receiver(
    export_country_delete_signal,
    sender=CompanyExportCountry,
    dispatch_uid='record_export_country_history_delete',
)
def record_export_country_history_delete(sender, instance, by, **kwargs):
    """
    Record export country deletions to history.
    """
    action = CompanyExportCountryHistory.HistoryType.DELETE
    _record_export_country_history(instance, action, by)


def _record_export_country_history(export_country, action, adviser):
    """
    Records each change made to `CompanyExportCountry` model
    into companion log model, `CompanyExportCountryHistory`.
    Along with type of change, insert, update or delete.
    """
    CompanyExportCountryHistory.objects.create(
        history_user=adviser,
        history_type=action,
        id=export_country.id,
        company=export_country.company,
        country=export_country.country,
        status=export_country.status,
    )
