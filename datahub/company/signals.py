import logging
from functools import partial

import reversion
from django.db import transaction
from django.db.models.signals import post_delete, post_migrate, post_save
from django.dispatch import receiver

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import Company, CompanyExportCountry
from datahub.company.notify import notify_new_dnb_investigation
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
    post_save,
    sender=CompanyExportCountry,
    dispatch_uid='add_company_to_revision_after_post_export_country_save',
)
def _add_company_to_revision_post_save(sender, instance, created, raw, **kwargs):
    """
    Explicitly add company to revision after a CompanyExportCountry has been saved.
    This is similar to using the follow='company' option when registering
    CompanyExportCountry with reversion. However, there is an important difference.
    With the latter, if the company happens to be saved first and then a CompanyExportCountry
    is saved later within the save revision context, the company's serialization will not be
    recomputed.
    Since the future_interest_countries field in the serialized format is computed by a
    model method, relying on the 'follow' option would have the effect that the
    future_interest_countries field in the serialized_data would reflect an old version
    of the data, before the CompanyExportCountry was saved.
    """
    if reversion.is_active():
        reversion.add_to_revision(instance.company)


@receiver(
    post_delete,
    sender=CompanyExportCountry,
    dispatch_uid='add_company_to_revision_after_post_export_country_delete',
)
def _add_company_to_revision_post_delete(sender, instance, using, **kwargs):
    """
    Explicitly add company to revision after a CompanyExportCountry has been deleted.
    See comment above for _add_company_to_revision_post_save.
    """
    if reversion.is_active():
        reversion.add_to_revision(instance.company)
