import logging

from django.db.models.signals import post_migrate, post_save, pre_save
from django.dispatch import receiver

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import (
    CompanyExportCountry,
    CompanyExportCountryHistory,
    Contact,
)
from datahub.company.models.company import Company
from datahub.company.signal_receivers import (
    export_country_delete_signal,
    export_country_update_signal,
)
from datahub.company_activity.models import PromptPayments
from datahub.core.utils import load_constants_to_database
from datahub.metadata.models import BusinessType
from datahub.search.company.tasks import schedule_sync_investment_projects_of_subsidiary_companies

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Company)
def company_one_list_account_owner_changed(sender, instance, **kwargs):
    try:
        original = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if original.one_list_account_owner_id is not instance.one_list_account_owner_id:
            schedule_sync_investment_projects_of_subsidiary_companies(
                instance,
                original.modified_on,
            )


@receiver(
    post_migrate,
    sender=BusinessType._meta.app_config,
    dispatch_uid='company_business_type_post_migrate',
)
def company_business_type_post_migrate(sender, **kwargs):
    """Ensures all business types are loaded to the database.

    Any new business types are created, and any existing ones are updated if the label has changed.
    """
    load_constants_to_database(BusinessTypeConstant, BusinessType)


@receiver(
    export_country_update_signal,
    sender=CompanyExportCountry,
    dispatch_uid='record_export_country_history_update',
)
def record_export_country_history_update(sender, instance, created, by, **kwargs):
    """Record export country changes to history."""
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
    """Record export country deletions to history."""
    action = CompanyExportCountryHistory.HistoryType.DELETE
    _record_export_country_history(instance, action, by)


def _record_export_country_history(export_country, action, adviser):
    """Records each change made to `CompanyExportCountry` model
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


@receiver(post_save, sender=Company, dispatch_uid='link_prompt_payments_on_company_save')
def link_prompt_payments_on_company_save(sender, instance, created, **kwargs):
    """After a Company is saved:
    1. Link unlinked PromptPayment records if company_house_number matches.
    2. For PromptPayment records now linked to this company, try to link their contact
       if email_address matches a contact within this company.
    """
    if instance.company_number:
        unlinked_prompt_payments = PromptPayments.objects.filter(
            company_house_number=instance.company_number,
            company__isnull=True,
        )

        if unlinked_prompt_payments.exists():
            num_updated = unlinked_prompt_payments.update(company=instance)
            logger.info(
                f'{num_updated} PromptPayment record(s) linked to Company {instance.pk} '
                f'(CHN: {instance.company_number}) on company save.',
            )

    prompt_payments_to_check_contact = PromptPayments.objects.filter(
        company=instance,
        contact__isnull=True,
        email_address__isnull=False,
    ).exclude(email_address__exact='')

    for pp_record in prompt_payments_to_check_contact:
        try:
            contact_to_link = Contact.objects.get(
                company=instance,
                email__iexact=pp_record.email_address,
            )
            pp_record.contact = contact_to_link
            pp_record.save(update_fields=['contact', 'modified_on', 'modified_by'])
            logger.info(
                f'PromptPayment record {pp_record.source_id} linked to Contact {contact_to_link.pk} '
                f'(Email: {pp_record.email_address}) in Company {instance.pk}.',
            )
        except Contact.DoesNotExist:
            logger.debug(
                f'No contact found with email "{pp_record.email_address}" in Company {instance.pk} '
                f'for PromptPayment source_id {pp_record.source_id}.',
            )
        except Contact.MultipleObjectsReturned:
            logger.warning(
                f'Multiple contacts found with email "{pp_record.email_address}" in Company {instance.pk} '
                f'for PromptPayment source_id {pp_record.source_id}. Contact not linked to avoid ambiguity.',
            )
        except Exception as e:
            logger.error(
                f'Error linking contact for PromptPayment source_id {pp_record.source_id}: {e}',
            )
