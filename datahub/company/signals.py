import logging
from functools import partial

from django.db import transaction
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import (
    Company,
    CompanyExportCountry,
    CompanyExportCountryHistory,
)
from datahub.company.notify import notify_new_dnb_investigation
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


# TODO: Remove this once the API endpoint for creating D&B investigations is released
@receiver(
    post_save,
    sender=Company,
    dispatch_uid='notify_dnb_investigation_post_save',
)
def notify_dnb_investigation_post_save(sender, instance, created, raw, **kwargs):
    """
    Notify recipients of a new company that needs investigation by DNB. This will only be triggered
    for a company which has `pending_dnb_investigation=True` and was not created
    through a data fixture (or similar).
    """
    if raw:
        return

    if created and instance.pending_dnb_investigation:
        transaction.on_commit(partial(_notify_dnb_investigation_post_save, instance))


def _notify_dnb_investigation_post_save(instance):
    logger.info(f'Company with ID {instance.id} is pending DNB investigation.')
    notify_new_dnb_investigation(instance)


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
