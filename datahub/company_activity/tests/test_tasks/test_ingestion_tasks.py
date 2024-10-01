import importlib
import sys

from unittest.mock import patch

import boto3
import pytest

from django.conf import settings
from moto import mock_aws

from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from datahub.company_activity.models import IngestedFile
from datahub.company_activity.tasks import GreatIngestionTask
from datahub.company_activity.tasks.ingest_company_activity import (
    BUCKET, CompanyActivityIngestionTask, GREAT_PREFIX, REGION,
)
from datahub.core.queues.constants import EVERY_TEN_MINUTES
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import DataHubScheduler


@pytest.fixture
def test_files():
    files = [
        '20240918T000000/full_ingestion.jsonl.gz',
        '20240920T000000/full_ingestion.jsonl.gz',
        '20240919T000000/full_ingestion.jsonl.gz',
        '20230919T000000/full_ingestion.jsonl.gz',
        '20240419T120000/full_ingestion.jsonl.gz',
    ]
    return list(map(lambda x: GREAT_PREFIX + x, files))


@mock_aws
def setup_s3_bucket(bucket_name, test_files):
    mock_s3_client = boto3.client('s3', REGION)
    mock_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': REGION},
    )
    for file in test_files:
        mock_s3_client.put_object(Bucket=bucket_name, Key=file, Body='Test contents')


class TestCompanyActivityIngestionTasks:
    @patch('os.system')
    def test_company_activity_ingestion_task_schedule(self, mock_system):
        """
        Test that a task is scheduled to check for new Company Activity data
        """
        # Import inside test to prevent the os.system call from running before the patch
        cron = importlib.import_module('cron-scheduler')
        cron.schedule_jobs()
        queue = 'long-running'

        scheduler = Scheduler(queue, connection=Redis.from_url(settings.REDIS_BASE_URL))
        scheduled_jobs = scheduler.get_jobs()
        ingestion_task = (
            'datahub.company_activity.tasks.ingest_company_activity.'
            'CompanyActivityIngestionTask.ingest_activity_data'
        )
        scheduled_job = [job for job in scheduled_jobs if job.func_name == ingestion_task][0]
        assert scheduled_job.func_name == ingestion_task
        assert scheduled_job.meta['cron_string'] == EVERY_TEN_MINUTES

        # Prevents the scheduler loop from running after tests finish by unloading the module again
        sys.modules.pop('cron-scheduler')

    @pytest.mark.django_db
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_ingestion_job_is_queued_for_new_files(self, mock, test_files):
        """
        Test that when a new file is found a job is queued to ingest it
        and no jobs are created for files that have already been ingested
        """
        new_file = GREAT_PREFIX + '20240920T000000/full_ingestion.jsonl.gz'
        setup_s3_bucket(BUCKET, test_files)
        for file in test_files:
            if not file == new_file:
                IngestedFile.objects.create(filepath=file)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count

        task = CompanyActivityIngestionTask()
        task.ingest_activity_data()
        assert rq_queue.count == initial_job_count + 1
        jobs = rq_queue.jobs
        job = jobs[-1]
        assert job.func_name == 'ingest'
        assert job.kwargs['bucket'] == BUCKET
        assert job.kwargs['file'] == new_file

    @pytest.mark.django_db
    # Patch so that we can simulate a job on the queue rather than having it run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_duplicate_ingestion_jobs_are_not_queued(self, mock, test_files):
        """
        Test that when, the job has run and queued an ingestion job for a file
        but that child job hasn't completed yet, this job does not queue a duplicate
        when running again
        """
        new_file = GREAT_PREFIX + '20240920T000000/full_ingestion.jsonl.gz'
        setup_s3_bucket(BUCKET, test_files)
        for file in test_files:
            if not file == new_file:
                IngestedFile.objects.create(filepath=file)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        job_scheduler(
            function=GreatIngestionTask().ingest,
            function_kwargs={'bucket': BUCKET, 'file': new_file},
            queue_name='long-running',
            description='Ingest Great data file',
        )
        initial_job_count = rq_queue.count

        task = CompanyActivityIngestionTask()
        task.ingest_activity_data()
        assert rq_queue.count == initial_job_count
