import logging
from unittest import mock

import pytest
from django.test import override_settings
from moto import mock_aws

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.company_activity.models import PromptPayments
from datahub.company_activity.tasks.constants import PROMPT_PAYMENTS_PREFIX
from datahub.company_activity.tasks.ingest_prompt_payments import (
    PromptPaymentsIngestionTask,
    prompt_payments_identification_task,
    prompt_payments_ingestion_task,
)
from datahub.company_activity.tests.factories import PromptPaymentsFactory
from datahub.ingest.models import IngestedObject
from datahub.ingest.utils import compressed_json_faker, upload_objects_to_s3

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_s3_object_processor(s3_object_processor):
    s3_object_processor.prefix = PROMPT_PAYMENTS_PREFIX
    return s3_object_processor


@mock_aws
class TestPromptPaymentIngestionTask:
    """Tests for PromptPaymentsIngestionTask."""

    def _get_base_record_data(self, source_id=1):
        return {
            'id': source_id,
            'reporting_period_start_date': '2025-01-01',
            'reporting_period_end_date': '2025-03-31',
            'filing_date': '2025-04-15',
            'company_name': 'Test Company Ltd',
            'company_id': '12345678',
            'email_address': 'test@example.com',
            'approved_by': 'John Doe',
            'qualifying_contracts_in_period': True,
            'average_paid_days': 25,
            'paid_within_30_days_pct': 80,
            'paid_31_to_60_days_pct': 15,
            'paid_after_61_days_pct': 5,
            'paid_later_than_terms_pct': 2,
            'payment_shortest_period_days': 10,
            'payment_longest_period_days': 45,
            'payment_max_period_days': 60,
            'payment_terms_changed_comment': 'No changes.',
            'payment_terms_changed_notified_comment': 'N/A',
            'code_of_practice': 'PPC',
            'other_electronic_invoicing': False,
            'other_supply_chain_finance': False,
            'other_retention_charges_in_policy': False,
            'other_retention_charges_in_past': False,
        }

    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_ingestion_task_full_flow(self, caplog, mock_s3_object_processor):
        """Test the full flow from identification to ingestion."""
        caplog.set_level(logging.INFO)
        object_key = f'{PROMPT_PAYMENTS_PREFIX}test_file.jsonl.gz'
        record_data = self._get_base_record_data()
        s3_content = compressed_json_faker([record_data])
        upload_objects_to_s3(mock_s3_object_processor, [(object_key, s3_content)])

        prompt_payments_identification_task()
        assert f'Scheduled ingestion of {object_key}' in caplog.text

        # simulate ingestion task
        prompt_payments_ingestion_task(object_key)
        assert f'Prompt payments ingestion task finished for file {object_key}' in caplog.text

        assert PromptPayments.objects.count() == 1
        pp_record = PromptPayments.objects.first()
        assert pp_record.source_id == record_data['id']
        assert pp_record.company_name == record_data['company_name']
        assert pp_record.company_house_number == record_data['company_id']
        assert pp_record.email_address == record_data['email_address']
        assert IngestedObject.objects.filter(object_key=object_key).exists()

    def test_process_record_creates_new_prompt_payment(self, mock_s3_object_processor):
        """Test that a new PromptPayments record is created."""
        task = PromptPaymentsIngestionTask('dummy_key', mock_s3_object_processor)
        record_data = self._get_base_record_data()

        task._process_record(record_data)

        assert PromptPayments.objects.count() == 1
        pp_record = PromptPayments.objects.first()
        assert pp_record.source_id == record_data['id']
        assert pp_record.company_name == record_data['company_name']
        assert pp_record.average_paid_days == record_data['average_paid_days']
        assert len(task.created_ids) == 1
        assert len(task.updated_ids) == 0

    def test_process_record_updates_existing_prompt_payment(self, mock_s3_object_processor):
        """Test that an existing PromptPayments record is updated."""
        task = PromptPaymentsIngestionTask('dummy_key', mock_s3_object_processor)
        prompt_payment = PromptPaymentsFactory()
        task.existing_ids = {prompt_payment.source_id}

        updated_record_data = self._get_base_record_data(source_id=prompt_payment.source_id)
        updated_record_data['average_paid_days'] = 30

        # override _should_process_record to force update for testing
        with mock.patch.object(task, '_should_process_record', return_value=True):
            task._process_record(updated_record_data)

        assert PromptPayments.objects.count() == 1
        pp_record = PromptPayments.objects.first()
        assert pp_record.source_id == updated_record_data['id']
        assert pp_record.average_paid_days == 30
        assert len(task.created_ids) == 0
        assert len(task.updated_ids) == 1

    def test_company_linking_by_chn(self, mock_s3_object_processor):
        """Test company is linked if CHN matches."""
        task = PromptPaymentsIngestionTask('dummy_key', mock_s3_object_processor)
        company = CompanyFactory(company_number='CH123')
        record_data = self._get_base_record_data()
        record_data['company_id'] = 'CH123'

        task._process_record(record_data)
        pp_record = PromptPayments.objects.first()
        assert pp_record.company == company

    def test_company_linking_by_name(self, mock_s3_object_processor):
        """Test company is linked by name if CHN doesn't match but name does."""
        task = PromptPaymentsIngestionTask('dummy_key', mock_s3_object_processor)
        company = CompanyFactory(name='Test Company Ltd', company_number='OTHER_CH')
        record_data = self._get_base_record_data()
        record_data['company_id'] = 'NON_MATCHING_CH'
        record_data['company_name'] = 'Test Company Ltd'

        task._process_record(record_data)
        pp_record = PromptPayments.objects.first()
        assert pp_record.company == company

    def test_contact_linking_within_company(self, mock_s3_object_processor):
        """Test contact is linked if email matches within the linked company."""
        task = PromptPaymentsIngestionTask('dummy_key', mock_s3_object_processor)
        company = CompanyFactory(company_number='CH123')
        contact = ContactFactory(company=company, email='test@example.com')
        record_data = self._get_base_record_data()
        record_data['company_id'] = 'CH123'
        record_data['email_address'] = 'test@example.com'

        task._process_record(record_data)
        pp_record = PromptPayments.objects.first()
        assert pp_record.contact == contact
        assert pp_record.company == company

    def test_no_company_or_contact_linking_if_unmatched(self, mock_s3_object_processor):
        """Test company and contact FKs are None if no match found."""
        task = PromptPaymentsIngestionTask('dummy_key', mock_s3_object_processor)
        record_data = self._get_base_record_data()
        record_data['company_id'] = 'UNMATCHED_CH'
        record_data['company_name'] = 'UNMATCHED_NAME'
        record_data['email_address'] = 'unmatched_contact@example.com'

        task._process_record(record_data)
        pp_record = PromptPayments.objects.first()
        assert pp_record.company is None
        assert pp_record.contact is None

    def test_should_process_record_skips_existing_source_id(self, mock_s3_object_processor):
        """Test _should_process_record correctly skips existing source_ids."""
        task = PromptPaymentsIngestionTask('dummy_key', mock_s3_object_processor)
        prompt_payment = PromptPaymentsFactory()
        task.existing_ids = {prompt_payment.source_id}

        assert not task._should_process_record(
            {'id': prompt_payment.source_id, 'filing_date': str(prompt_payment.filing_date)},
        )
        assert task._should_process_record({'id': 456, 'filing_date': '2025-01-01'})
