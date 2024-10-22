import importlib
import logging
import sys

from datetime import (
    datetime,
    timedelta,
)
from unittest.mock import patch

import pytest

from django.conf import settings
from moto import mock_aws
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler


from datahub.company_activity.models import IngestedFile
from datahub.company_activity.tests.factories import CompanyActivityIngestedFileFactory
from datahub.core import constants
from datahub.core.queues.constants import EVERY_HOUR
from datahub.core.queues.scheduler import DataHubScheduler
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BUCKET,
    DATE_FORMAT,
)
from datahub.investment_lead.tasks.ingest_eyb_triage import (
    ingest_eyb_triage_data,
    ingest_eyb_triage_file,
    TRIAGE_PREFIX,
)
from datahub.investment_lead.test.factories import (
    eyb_lead_triage_record_faker,
    EYBLeadFactory,
    generate_hashed_uuid,
)
from datahub.investment_lead.test.test_tasks.utils import (
    file_contents_faker,
    setup_s3_bucket,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_triage_file_path():
    return f'{TRIAGE_PREFIX}/triage.jsonl.gz'


@pytest.fixture
def test_triage_file_paths():
    file_names = [
        '1.jsonl.gz',
        '2.jsonl.gz',
        '3.jsonl.gz',
        '4.jsonl.gz',
        '5.jsonl.gz',
    ]
    return list(map(lambda x: TRIAGE_PREFIX + x, file_names))


class TestEYBTriageFileIngestionTasks:
    @patch('os.system')
    def test_triage_ingestion_job_is_scheduled(self, mock_system):
        # Import inside test to prevent the os.system call from running before the patch
        cron = importlib.import_module('cron-scheduler')
        cron.schedule_jobs()
        queue = 'short-running'

        scheduler = Scheduler(queue, connection=Redis.from_url(settings.REDIS_BASE_URL))
        scheduled_jobs = scheduler.get_jobs()
        func = 'datahub.investment_lead.tasks.ingest_eyb_triage.ingest_eyb_triage_file'
        scheduled_job = [job for job in scheduled_jobs if job.func_name == func][0]
        assert scheduled_job.meta['cron_string'] == EVERY_HOUR

        # Prevents the scheduler loop from running after tests finish by unloading the module again
        sys.modules.pop('cron-scheduler')

    @pytest.mark.django_db
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_ingestion_job_is_queued_for_new_triage_files(
        self, mock, test_triage_file_paths, caplog,
    ):
        """Tests that when a new file is found, a job is queued to ingest it."""
        new_file_path = TRIAGE_PREFIX + '5.jsonl.gz'
        setup_s3_bucket(BUCKET, test_triage_file_paths)
        for file_path in test_triage_file_paths:
            if not file_path == new_file_path:
                IngestedFile.objects.create(filepath=file_path)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count

        with caplog.at_level(logging.INFO):
            ingest_eyb_triage_file()
            assert 'Checking for new EYB triage files' in caplog.text
            assert f'Scheduled ingestion of {new_file_path}' in caplog.text

        assert rq_queue.count == initial_job_count + 1
        jobs = rq_queue.jobs
        job = jobs[-1]
        ingestion_task = 'datahub.investment_lead.tasks.ingest_eyb_triage.ingest_eyb_triage_data'
        assert job.func_name == ingestion_task
        assert job.kwargs['bucket'] == BUCKET
        assert job.kwargs['file'] == new_file_path


class TestEYBTriageDataIngestionTasks:
    @mock_aws
    def test_triage_file_is_ingested(self, caplog, test_triage_file_path):
        """
        Test that a EYB triage data file is ingested correctly and the ingested
        file is added to the IngestedFile table
        """
        initial_eyb_lead_count = EYBLead.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        file_contents = file_contents_faker(default_faker='triage')
        setup_s3_bucket(BUCKET, [test_triage_file_path], [file_contents])
        with caplog.at_level(logging.INFO):
            ingest_eyb_triage_data(BUCKET, test_triage_file_path)
            assert f'Ingesting file: {test_triage_file_path} started' in caplog.text
            assert f'Ingesting file: {test_triage_file_path} finished' in caplog.text
        assert EYBLead.objects.count() > initial_eyb_lead_count
        assert IngestedFile.objects.count() == initial_ingested_count + 1

    @mock_aws
    def test_triage_data_ingestion_updates_existing_fields(self, test_triage_file_path):
        """
        Test that for records which have been previously ingested, updated fields
        have their new values ingested
        """
        wales_id = constants.UKRegion.wales.value.id
        hashed_uuid = generate_hashed_uuid()
        EYBLeadFactory(triage_hashed_uuid=hashed_uuid, proposed_investment_region_id=wales_id)
        assert EYBLead.objects.count() == 1
        records = [
            eyb_lead_triage_record_faker({
                'hashedUuid': hashed_uuid,
                'location': constants.UKRegion.northern_ireland.value.name,
            }),
        ]
        file_contents = file_contents_faker(records)
        setup_s3_bucket(BUCKET, [test_triage_file_path], [file_contents])
        ingest_eyb_triage_data(BUCKET, test_triage_file_path)
        assert EYBLead.objects.count() == 1
        updated = EYBLead.objects.get(triage_hashed_uuid=hashed_uuid)
        assert str(updated.proposed_investment_region.id) == \
            constants.UKRegion.northern_ireland.value.id

    @mock_aws
    def test_unmodified_triage_records_are_skipped_during_ingestion(self):
        """
        Test that we skip updating records whose modified date is older than the last
        file ingestion date
        """
        hashed_uuid = generate_hashed_uuid()
        yesterday = datetime.strftime(datetime.now() - timedelta(1), DATE_FORMAT)
        file_path = f'{TRIAGE_PREFIX}1.jsonl.gz'
        new_file_path = f'{TRIAGE_PREFIX}2.jsonl.gz'
        CompanyActivityIngestedFileFactory(
            created_on=datetime.now(),
            filepath=file_path,
        )
        records = [
            {
                'hashedUuid': hashed_uuid,
                'created': yesterday,
                'modified': yesterday,
                'sector': 'Mining',
            },
        ]
        file_contents = file_contents_faker(records)
        setup_s3_bucket(BUCKET, [new_file_path], [file_contents])
        ingest_eyb_triage_data(BUCKET, new_file_path)
        assert EYBLead.objects.count() == 0

    @mock_aws
    def test_incoming_triage_records_trigger_correct_logging(self, caplog):
        """Test that incoming triage correct logging messages.

        If created -> hashed uuid is in the created list;
        If updated existing record -> hashed uuid is in the updated list;
        If failed validation -> errors captured in the error list.
        """
        today = datetime.now()
        yesterday = datetime.now() - timedelta(days=1)

        created_hashed_uuid = generate_hashed_uuid()
        updated_hashed_uuid = generate_hashed_uuid()
        failed_hashed_uuid = generate_hashed_uuid()

        EYBLeadFactory(
            triage_hashed_uuid=updated_hashed_uuid,
            sector_id=constants.Sector.defence.value.id,
        )
        assert EYBLead.objects.count() == 1

        records = [
            # Created record
            eyb_lead_triage_record_faker({
                'hashedUuid': created_hashed_uuid,
                'created': today,
                'modified': today,
            }),
            # Updated record
            {
                'hashedUuid': updated_hashed_uuid,
                'created': yesterday,
                'modified': today,
                'sector': 'Mining',
            },
            # Failed record
            {
                'hashedUuid': failed_hashed_uuid,
                'created': today,
                'modified': today,
            },
        ]

        file_path = f'{TRIAGE_PREFIX}1.jsonl.gz'
        CompanyActivityIngestedFileFactory(
            created_on=yesterday,
            filepath=file_path,
        )
        file_contents = file_contents_faker(records)
        setup_s3_bucket(BUCKET, [file_path], [file_contents])
        with caplog.at_level(logging.INFO):
            ingest_eyb_triage_data(BUCKET, file_path)
            assert f"1 records created: ['{created_hashed_uuid}']" in caplog.text
            assert f"1 records updated: ['{updated_hashed_uuid}']" in caplog.text
            assert '1 records failed validation:' in caplog.text
            assert f"'index': '{failed_hashed_uuid}'" in caplog.text
            assert 'sector' in caplog.text
            assert 'This field is required.' in caplog.text
        assert EYBLead.objects.count() == 2
