import importlib
import logging
import sys

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import boto3
import pytest

from django.conf import settings
from moto import mock_aws
from redis import Redis
from rq import Queue, Worker
from rq.job import Job
from rq_scheduler import Scheduler


from datahub.company_activity.models import IngestedFile
from datahub.company_activity.tests.factories import CompanyActivityIngestedFileFactory
from datahub.core import constants
from datahub.core.queues.constants import EVERY_HOUR
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import DataHubScheduler
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import CreateEYBLeadTriageSerializer
from datahub.investment_lead.tasks.ingest_common import (
    BUCKET,
    DATE_FORMAT,
    REGION,
)
from datahub.investment_lead.tasks.ingest_eyb_triage import (
    EYBTriageDataIngestionTask,
    ingest_eyb_triage_file,
    ingest_eyb_triage_data,
    TRIAGE_PREFIX,
)
from datahub.investment_lead.test.factories import (
    create_fake_file,
    eyb_lead_triage_record_faker,
    EYBLeadFactory,
    generate_hashed_uuid,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_file_path():
    return f'{TRIAGE_PREFIX}/triage.jsonl.gz'


@pytest.fixture
def test_file_paths():
    file_names = [
        '1.jsonl.gz',
        '2.jsonl.gz',
        '3.jsonl.gz',
        '4.jsonl.gz',
        '5.jsonl.gz',
    ]
    return list(map(lambda x: TRIAGE_PREFIX + x, file_names))


@mock_aws
def setup_s3_client():
    return boto3.client('s3', REGION)


@mock_aws
def setup_s3_bucket(bucket_name, test_file_paths, test_file_contents = None):
    mock_s3_client = boto3.client('s3', REGION)
    mock_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': REGION},
    )
    if test_file_contents is None:
        test_file_contents = [create_fake_file() for _ in range(len(test_file_paths))]
    for file_path, file_contents in zip(test_file_paths, test_file_contents):
        mock_s3_client.put_object(Bucket=bucket_name, Key=file_path, Body=file_contents)


class TestEYBTriageFileIngestionTasks:
    @patch('os.system')
    def test_eyb_triage_ingestion_task_schedule(self):
        """
        Test that a task is scheduled to check for new EYB triage data
        """
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
    def test_ingestion_job_is_queued_for_new_files(self, test_file_paths, caplog):
        """
        Test that when a new file is found a job is queued to ingest it
        and no jobs are created for files not the most recent
        """
        new_file_path = TRIAGE_PREFIX + '6.jsonl.gz'
        setup_s3_bucket(BUCKET, test_file_paths)
        for file_path in test_file_paths:
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

    @pytest.mark.django_db
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_ingestion_job_is_not_queued_for_already_ingested_file(self, test_file_paths, caplog):
        """
        Test that when the latest file found has already been ingested no job is queued
        """
        ingested_file_path = TRIAGE_PREFIX + '5.jsonl.gz'  # this exists in the test_file_paths fixture
        setup_s3_bucket(BUCKET, test_file_paths)
        for file_path in test_file_paths:
            IngestedFile.objects.create(filepath=file_path)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count

        with caplog.at_level(logging.INFO):
            ingest_eyb_triage_file()
            assert f'{ingested_file_path} has already been ingested' in caplog.text
        assert rq_queue.count == initial_job_count

    @pytest.mark.django_db
    # Patch so that we can simulate a job on the queue rather than having it run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_job_not_queued_when_already_on_queue(self, test_file_paths, caplog):
        """
        Test that when, the job has run and queued an ingestion job for a file
        but that child job hasn't completed yet, this job does not queue a duplicate
        when running again
        """
        new_file_path = TRIAGE_PREFIX + '6.jsonl.gz'
        setup_s3_bucket(BUCKET, test_file_paths)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        job_scheduler(
            function=ingest_eyb_triage_data,
            function_kwargs={'bucket': BUCKET, 'file': new_file_path},
            queue_name='long-running',
            description='Ingest EYB data.',
        )
        initial_job_count = rq_queue.count

        with caplog.at_level(logging.INFO):
            ingest_eyb_triage_file()
            assert f'{new_file_path} has already been queued for ingestion' in caplog.text
        assert rq_queue.count == initial_job_count

    @pytest.mark.django_db
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @patch('datahub.investment_lead.tasks.ingest_eyb_triage.Worker')
    @mock_aws
    def test_job_not_queued_when_already_running(self, mock_worker, test_file_paths):
        """
        Test that we don't queue a job to ingest a file when a job is already running for it
        """
        new_file_path = TRIAGE_PREFIX + '6.jsonl.gz'
        setup_s3_bucket(BUCKET, test_file_paths)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count
        func = 'datahub.investment_lead.tasks.ingest_eyb_triage.ingest_eyb_triage_data'
        mock_job = Job.create(func, kwargs={'file': new_file_path}, connection=redis)
        mock_worker_instance = Worker(['long-running'], connection=redis)
        mock_worker_instance.get_current_job = MagicMock(return_value=mock_job)
        mock_worker.all.return_value = [mock_worker_instance]

        ingest_eyb_triage_file()
        assert rq_queue.count == initial_job_count


class TestEYBTriageDataIngestionTasks:
    @mock_aws
    def test_eyb_triage_file_ingestion(self, caplog, test_file_path):
        """
        Test that a EYB triage data file is ingested correctly and the ingested
        file is added to the IngestedFile table
        """
        initial_eyb_lead_count = EYBLead.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        setup_s3_bucket(BUCKET, [test_file_path])
        with caplog.at_level(logging.INFO):
            ingest_eyb_triage_data(BUCKET, test_file_path)
            assert f'Ingesting file: {test_file_path} started' in caplog.text
            assert f'Ingesting file: {test_file_path} finished' in caplog.text
        assert EYBLead.objects.count() > initial_eyb_lead_count
        assert IngestedFile.objects.count() == initial_ingested_count + 1

    def test_get_last_ingestion_datetime_of_triage_data(self):
        triage_filepath_1 = 'data-flow/eyb-triage-pipeline/1.jsonl.gz'
        triage_filepath_2 = 'data-flow/eyb-triage-pipeline/2.jsonl.gz'
        user_filepath = 'data-flow/eyb-user-pipeline/1.jsonl.gz'

        CompanyActivityIngestedFileFactory(
            filepath=triage_filepath_1,
            created_on=datetime.now() - timedelta(days=2),
        )
        most_recent_triage_file = CompanyActivityIngestedFileFactory(
            filepath=triage_filepath_2,
            created_on=datetime.now() - timedelta(days=1),
        )
        CompanyActivityIngestedFileFactory(
            filepath=user_filepath,
            created_on=datetime.now(),
        )

        last_triage_ingestion_datetime = EYBTriageDataIngestionTask(
            serializer_class=CreateEYBLeadTriageSerializer,
            prefix='data-flow/eyb-triage-pipeline',
        )._last_ingestion_datetime

        assert last_triage_ingestion_datetime == most_recent_triage_file.created_on

    @mock_aws
    def test_eyb_triage_data_ingestion_updates_existing(self, test_file_path):
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
        file = create_fake_file(records)
        setup_s3_bucket(BUCKET, [test_file_path], [file])
        ingest_eyb_triage_data(BUCKET, test_file_path)
        assert EYBLead.objects.count() == 1
        updated = EYBLead.objects.get(triage_hashed_uuid=hashed_uuid)
        assert str(updated.proposed_investment_region.id) == \
            constants.UKRegion.northern_ireland.value.id

    @mock_aws
    def test_skip_unchanged_records(self, test_file_path):
        """
        Test that we skip updating records whose modified date is older than the last
        file ingestion date
        """
        hashed_uuid = generate_hashed_uuid()
        yesterday = datetime.strftime(datetime.now() - timedelta(1), DATE_FORMAT)
        CompanyActivityIngestedFileFactory(created_on=datetime.now(), filepath=test_file_path)
        records = [
            {
                'hashedUuid': hashed_uuid,
                'created': yesterday,
                'modified': yesterday,
                'sector': 'Mining',
                'sectorSub': 'Mining vehicles, transport and equipment',
            },
        ]
        file = create_fake_file(records)
        setup_s3_bucket(BUCKET, [test_file_path], [file])
        ingest_eyb_triage_data(BUCKET, test_file_path)
        assert EYBLead.objects.count() == 0

    @mock_aws
    def test_invalid_file(self, test_file_path):
        """
        Test that an exception is raised when the file is not valid
        """
        mock_s3_client = setup_s3_client()
        mock_s3_client.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={'LocationConstraint': REGION},
        )
        with pytest.raises(Exception) as e:
            ingest_eyb_triage_data(BUCKET, test_file_path)
        exception = e.value.args[0]
        assert 'The specified key does not exist' in exception
        expected = f"key: '{test_file_path}'"
        assert expected in exception
