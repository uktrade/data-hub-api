import logging

from datahub.company.models import Company, Contact
from datahub.company_activity.models import PromptPayments
from datahub.company_activity.tasks.constants import PROMPT_PAYMENTS_PREFIX
from datahub.core.queues.constants import THIRTY_MINUTES_IN_SECONDS
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import BaseObjectIdentificationTask, BaseObjectIngestionTask

logger = logging.getLogger(__name__)


def prompt_payments_identification_task() -> None:
    logger.info('Prompt payments identification task started.')
    identification_task = PromptPaymentsIdentificationTask(
        prefix=PROMPT_PAYMENTS_PREFIX,
        job_timeout=THIRTY_MINUTES_IN_SECONDS,
    )
    identification_task.identify_new_objects(prompt_payments_ingestion_task)
    logger.info('Prompt payments identification task finished.')


def prompt_payments_ingestion_task(object_key: str) -> None:
    logger.info(f'Prompt payments ingestion task started for file {object_key}.')
    ingestion_task = PromptPaymentsIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=PROMPT_PAYMENTS_PREFIX),
    )
    ingestion_task.ingest_object()
    logger.info(f'Prompt payments ingestion task finished for file {object_key}.')


class PromptPaymentsIdentificationTask(BaseObjectIdentificationTask):
    pass


class PromptPaymentsIngestionTask(BaseObjectIngestionTask):
    existing_ids = []

    def _should_process_record(self, record: dict) -> bool:
        if not self.existing_ids:
            self.existing_ids = set(
                PromptPayments.objects.values_list('source_id', flat=True),
            )

        source_id = record.get('id')
        if source_id in self.existing_ids:
            logger.info(f'Record already exists for prompt payments source_id: {source_id}')
            return False
        return True

    def _get_modified_datetime_str(self, record: dict) -> str:
        return record['filing_date']

    def _get_company(self, company_house_number, company_name, source_id):  # noqa
        """Attempts to find a company, prioritizing non-archived records.
        1. By non-archived Company House Number.
        2. By non-archived Company Name (if CHN not found or no match).
        3. By archived Company House Number (if no non-archived CHN match).
        4. By archived Company Name (if no non-archived CHN/Name match and no archived CHN match).
        """
        company = None

        if company_house_number:
            try:
                company = Company.objects.get(company_number=company_house_number, archived=False)
                logger.info(
                    f'Found non-archived company by CHN {company_house_number} for source_id {source_id}.',
                )
                return company
            except Company.DoesNotExist:
                pass
            except Company.MultipleObjectsReturned:
                logger.warning(
                    f'Multiple non-archived companies found for CHN {company_house_number} '
                    f'for prompt payment source_id {source_id}. Skipping company linking for CHN.',
                )

        if company_name:
            companies_by_name = Company.objects.filter(name=company_name, archived=False)
            if companies_by_name.count() == 1:
                company = companies_by_name.first()
                logger.info(
                    f'Found non-archived company by name "{company_name}" for source_id {source_id}.',
                )
                return company
            elif companies_by_name.count() > 1:
                logger.warning(
                    f'Multiple non-archived companies found for name "{company_name}" '
                    f'for prompt payment source_id {source_id}. Skipping company linking for name.',
                )

        if company_house_number:
            archived_companies_by_chn = Company.objects.filter(
                company_number=company_house_number,
                archived=True,
            )
            if archived_companies_by_chn.count() == 1:
                company = archived_companies_by_chn.first()
                logger.info(
                    f'Found archived company by CHN {company_house_number} for source_id {source_id}.',
                )
                return company
            elif archived_companies_by_chn.count() > 1:
                logger.warning(
                    f'Multiple archived companies found for CHN {company_house_number} '
                    f'for prompt payment source_id {source_id}. Skipping company linking for CHN.',
                )

        if company_name:
            archived_companies_by_name = Company.objects.filter(name=company_name, archived=True)
            if archived_companies_by_name.count() == 1:
                company = archived_companies_by_name.first()
                logger.info(
                    f'Found archived company by name "{company_name}" for source_id {source_id}.',
                )
                return company
            elif archived_companies_by_name.count() > 1:
                logger.warning(
                    f'Multiple archived companies found for name "{company_name}" '
                    f'for prompt payment source_id {source_id}. Skipping company linking for name.',
                )

        if not company:
            logger.info(
                f'No existing company found for source_id {source_id}. A new one might be created if data is sufficient or it will be ingested without a company link.',
            )
        return company

    def _process_record(self, record: dict) -> None:  # noqa
        source_id = record.get('id')
        company_house_number = record.get('company_id')
        company_name = record.get('company_name')
        email_address = record.get('email_address')

        company = self._get_company(company_house_number, company_name, source_id)

        contact = None
        if email_address:
            if company:
                contacts_in_company = Contact.objects.filter(
                    email__iexact=email_address,
                    company=company,
                )
                if contacts_in_company.count() > 1:
                    logger.warning(
                        f'Multiple contacts found for email {email_address} in company {company.id} '
                        f'for prompt payments source_id {source_id}. Using the first one found.',
                    )
                contact = contacts_in_company.first()
            else:
                contacts_by_email = Contact.objects.filter(email__iexact=email_address)
                if contacts_by_email.count() == 1:
                    contact = contacts_by_email.first()
                elif contacts_by_email.count() > 1:
                    logger.warning(
                        f'Multiple contacts found for email {email_address} (company unknown) '
                        f'for prompt payments source_id {source_id}. Contact not linked.',
                    )
        try:
            prompt_payments, created = PromptPayments.objects.update_or_create(
                source_id=source_id,
                defaults={
                    'reporting_period_start_date': record.get('reporting_period_start_date'),
                    'reporting_period_end_date': record.get('reporting_period_end_date'),
                    'filing_date': record.get('filing_date'),
                    'company_name': company_name or '',
                    'company_house_number': company_house_number or '',
                    'company': company,
                    'email_address': email_address or '',
                    'contact': contact,
                    'approved_by': record.get('approved_by', ''),
                    'qualifying_contracts_in_period': record.get(
                        'qualifying_contracts_in_period',
                        False,
                    ),
                    'average_paid_days': record.get('average_paid_days'),
                    'paid_within_30_days_pct': record.get('paid_within_30_days_pct'),
                    'paid_31_to_60_days_pct': record.get('paid_31_to_60_days_pct'),
                    'paid_after_61_days_pct': record.get('paid_after_61_days_pct'),
                    'paid_later_than_terms_pct': record.get('paid_later_than_terms_pct'),
                    'payment_shortest_period_days': record.get('payment_shortest_period_days'),
                    'payment_longest_period_days': record.get('payment_longest_period_days'),
                    'payment_max_period_days': record.get('payment_max_period_days'),
                    'payment_terms_changed_comment': record.get(
                        'payment_terms_changed_comment',
                        '',
                    ),
                    'payment_terms_changed_notified_comment': record.get(
                        'payment_terms_changed_notified_comment',
                        '',
                    ),
                    'code_of_practice': record.get('code_of_practice', ''),
                    'other_electronic_invoicing': record.get('other_electronic_invoicing', False),
                    'other_supply_chain_finance': record.get('other_supply_chain_finance', False),
                    'other_retention_charges_in_policy': record.get(
                        'other_retention_charges_in_policy',
                        False,
                    ),
                    'other_retention_charges_in_past': record.get(
                        'other_retention_charges_in_past',
                        False,
                    ),
                },
            )
            if created:
                self.created_ids.append(str(prompt_payments.id))
            else:
                self.updated_ids.append(str(prompt_payments.id))

        except Exception as e:
            logger.error(
                f'Error processing prompt payment record source_id: {source_id}. Error: {e}',
            )
            self.errors.append({'source_id': source_id, 'error': str(e)})
