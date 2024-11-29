import logging

from unittest.mock import patch

import pytest

from django.conf import settings
from moto import mock_aws
from redis import Redis
from rq import Queue


from datahub.company_activity.models import IngestedFile
from datahub.core.queues.scheduler import DataHubScheduler
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.tasks.ingest_eyb_common import BUCKET
from datahub.investment_lead.tasks.ingest_eyb_marketing import (
    ingest_eyb_marketing_data,
    ingest_eyb_marketing_file,
    MARKETING_PREFIX,
)
from datahub.investment_lead.tasks.ingest_eyb_user import (
    ingest_eyb_user_data,
    USER_PREFIX,
)
from datahub.investment_lead.test.factories import (
    eyb_lead_marketing_record_faker,
    EYBLeadFactory,
    generate_hashed_uuid,
)
from datahub.investment_lead.test.test_tasks.utils import (
    file_contents_faker,
    setup_s3_bucket,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_marketing_file_path():
    return f'{MARKETING_PREFIX}marketing.jsonl.gz'


@pytest.fixture
def test_marketing_file_paths():
    file_names = [
        '1.jsonl.gz',
        '2.jsonl.gz',
        '3.jsonl.gz',
        '4.jsonl.gz',
        '5.jsonl.gz',
    ]
    return list(map(lambda x: MARKETING_PREFIX + x, file_names))


class TestEYBMarketingFileIngestionTasks:

    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_marketing_ingestion_job_is_scheduled_after_user_ingestion_job_finishes(
        self, mock, caplog,
    ):
        """Test that a task is scheduled to check for new EYB marketing files.

        Unlike the EYB triage files, this task is not scheduled via cron-scheduler.py;
        rather, it is scheduled as part of a chain after successful completion of
        ingest_eyb_triage_data. This tests the last chain in the link from ingest_eyb_user_data
        to ingest_eyb_marketing_data.
        """
        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('short-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count

        file_path = f'{USER_PREFIX}user.jsonl.gz'
        file_contents = file_contents_faker(default_faker='user')
        setup_s3_bucket(BUCKET, [file_path], [file_contents])
        with caplog.at_level(logging.INFO):
            ingest_eyb_user_data(BUCKET, file_path)
            assert f'Ingesting file: {file_path} finished' in caplog.text
            assert 'Ingest EYB user data job has scheduled EYB marketing file job' in caplog.text

        assert rq_queue.count == initial_job_count + 1
        jobs = rq_queue.jobs
        job = jobs[-1]
        job_function_name = \
            'datahub.investment_lead.tasks.ingest_eyb_marketing.ingest_eyb_marketing_file'
        assert job.func_name == job_function_name

    @pytest.mark.django_db
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_ingestion_job_is_queued_for_new_marketing_files(
        self,
        mock,
        test_marketing_file_paths,
        caplog,
    ):
        """Tests that when a new file is found, a job is queued to ingest it."""
        new_file_path = MARKETING_PREFIX + '5.jsonl.gz'
        setup_s3_bucket(BUCKET, test_marketing_file_paths)
        for file_path in test_marketing_file_paths:
            if not file_path == new_file_path:
                IngestedFile.objects.create(filepath=file_path)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count

        with caplog.at_level(logging.INFO):
            ingest_eyb_marketing_file()
            assert 'Checking for new EYB marketing files' in caplog.text
            assert f'Scheduled ingestion of {new_file_path}' in caplog.text

        assert rq_queue.count == initial_job_count + 1
        jobs = rq_queue.jobs
        job = jobs[-1]
        ingestion_task = \
            'datahub.investment_lead.tasks.ingest_eyb_marketing.ingest_eyb_marketing_data'
        assert job.func_name == ingestion_task
        assert job.kwargs['bucket'] == BUCKET
        assert job.kwargs['file'] == new_file_path


class TestEYBMarketingDataIngestionTasks:
    @mock_aws
    def test_marketing_file_is_ingested(self, caplog, test_marketing_file_path):
        """
        Test that a EYB marketing data file is ingested correctly and the ingested
        file is added to the IngestedFile table
        """
        initial_eyb_lead_count = EYBLead.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        file_contents = file_contents_faker(default_faker='marketing')
        setup_s3_bucket(BUCKET, [test_marketing_file_path], [file_contents])
        with caplog.at_level(logging.INFO):
            ingest_eyb_marketing_data(BUCKET, test_marketing_file_path)
            assert f'Ingesting file: {test_marketing_file_path} started' in caplog.text
            assert f'Ingesting file: {test_marketing_file_path} finished' in caplog.text
        assert EYBLead.objects.count() > initial_eyb_lead_count
        assert IngestedFile.objects.count() == initial_ingested_count + 1

    @mock_aws
    def test_marketing_data_ingestion_does_not_update_existing(self, test_marketing_file_path):
        """Test previously ingested records do not trigger an update to the existing instance."""
        hashed_uuid = generate_hashed_uuid()
        initial_value = 'initial value'
        updated_value = 'updated value'
        EYBLeadFactory(marketing_hashed_uuid=hashed_uuid, utm_content=initial_value)
        assert EYBLead.objects.count() == 1
        records = [
            eyb_lead_marketing_record_faker({
                'hashed_uuid': hashed_uuid,
                'content': updated_value,
            }),
        ]
        file_contents = file_contents_faker(records)
        setup_s3_bucket(BUCKET, [test_marketing_file_path], [file_contents])
        ingest_eyb_marketing_data(BUCKET, test_marketing_file_path)
        assert EYBLead.objects.count() == 1
        updated = EYBLead.objects.get(marketing_hashed_uuid=hashed_uuid)
        assert updated.utm_content == initial_value

    @mock_aws
    def test_marketing_data_ingestion_does_not_fail_with_empty_records(
        self,
        test_marketing_file_path,
    ):
        """Test previously ingested records do not trigger an update to the existing instance."""
        hashed_uuid = generate_hashed_uuid()
        initial_value = 'initial value'
        EYBLeadFactory(marketing_hashed_uuid=hashed_uuid, utm_content=initial_value)
        assert EYBLead.objects.count() == 1
        records = []
        file_contents = file_contents_faker(records)
        setup_s3_bucket(BUCKET, [test_marketing_file_path], [file_contents])
        ingest_eyb_marketing_data(BUCKET, test_marketing_file_path)
        assert EYBLead.objects.count() == 1
        updated = EYBLead.objects.get(marketing_hashed_uuid=hashed_uuid)
        assert updated.utm_content == initial_value

    @mock_aws
    def test_incoming_marketing_records_trigger_correct_logging(self, caplog):
        """Test that incoming marketing correct logging messages.

        If created -> hashed uuid is in the created list;
        If updated existing record -> hashed uuid is in the updated list;
        If failed validation -> errors captured in the error list.
        """
        created_hashed_uuid = generate_hashed_uuid()
        updated_hashed_uuid = generate_hashed_uuid()

        # Existing leads with matching hashed uuids for triage or user component will be updated.
        # Existing leads with matching marketing hashed uuid will not be updated; this is because
        # marketing data is not updatable and so it would be an unnecessary overwrite.
        EYBLeadFactory(
            triage_hashed_uuid=updated_hashed_uuid,
            user_hashed_uuid=updated_hashed_uuid,
        )
        assert EYBLead.objects.count() == 1

        records = [
            # Created record
            eyb_lead_marketing_record_faker({
                'hashed_uuid': created_hashed_uuid,
            }),
            # Updated record
            eyb_lead_marketing_record_faker({
                'hashed_uuid': updated_hashed_uuid,
            }),
            # Failed record
            {},
        ]

        file_path = f'{MARKETING_PREFIX}1.jsonl.gz'
        file_contents = file_contents_faker(records)
        setup_s3_bucket(BUCKET, [file_path], [file_contents])
        with caplog.at_level(logging.INFO):
            ingest_eyb_marketing_data(BUCKET, file_path)
            assert f"1 records created: ['{created_hashed_uuid}']" in caplog.text
            assert f"1 records updated: ['{updated_hashed_uuid}']" in caplog.text
            assert '1 records failed validation:' in caplog.text
            assert "'index': None" in caplog.text
        assert EYBLead.objects.count() == 2
