import importlib
import logging
import sys

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
from datahub.company_activity.tasks import ingest_great_data
from datahub.company_activity.tasks.ingest_company_activity import (
    BUCKET, GREAT_PREFIX, ingest_activity_data, REGION,
)
from datahub.core.queues.constants import EVERY_HOUR
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
        func = 'datahub.company_activity.tasks.ingest_company_activity.ingest_activity_data'
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
    def test_ingestion_job_is_queued_for_new_files(self, mock, test_files):
        """
        Test that when a new file is found a job is queued to ingest it
        and no jobs are created for files not the most recent
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

        ingest_activity_data()
        assert rq_queue.count == initial_job_count + 1
        jobs = rq_queue.jobs
        job = jobs[-1]
        ingestion_task = 'datahub.company_activity.tasks.ingest_great_data.ingest_great_data'
        assert job.func_name == ingestion_task
        assert job.kwargs['bucket'] == BUCKET
        assert job.kwargs['file'] == new_file

    @pytest.mark.django_db
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_ingestion_job_is_not_queued_for_already_ingested_file(self, mock, test_files):
        """
        Test that when the latest file found has already been ingested no job is queued
        """
        setup_s3_bucket(BUCKET, test_files)
        for file in test_files:
            IngestedFile.objects.create(filepath=file)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count

        ingest_activity_data()
        assert rq_queue.count == initial_job_count

    @pytest.mark.django_db
    # Patch so that we can simulate a job on the queue rather than having it run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_job_not_queued_when_already_on_queue(self, mock, test_files):
        """
        Test that when, the job has run and queued an ingestion job for a file
        but that child job hasn't completed yet, this job does not queue a duplicate
        when running again
        """
        new_file = GREAT_PREFIX + '20240920T000000/full_ingestion.jsonl.gz'
        setup_s3_bucket(BUCKET, test_files)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        job_scheduler(
            function=ingest_great_data,
            function_kwargs={'bucket': BUCKET, 'file': new_file},
            queue_name='long-running',
            description='Ingest Great data file',
        )
        initial_job_count = rq_queue.count

        ingest_activity_data()
        assert rq_queue.count == initial_job_count

    @pytest.mark.django_db
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @patch('datahub.company_activity.tasks.ingest_company_activity.Worker')
    @mock_aws
    def test_job_not_queued_when_already_running(self, mock_worker, mock_scheduler, test_files):
        """
        Test that we don't queue a job to ingest a file when a job is already running for it
        """
        new_file = GREAT_PREFIX + '20240920T000000/full_ingestion.jsonl.gz'
        setup_s3_bucket(BUCKET, test_files)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count
        func = 'datahub.company_activity.tasks.ingest_great_data.ingest_great_data'
        mock_job = Job.create(func, kwargs={'file': new_file}, connection=redis)
        mock_worker_instance = Worker(['long-running'], connection=redis)
        mock_worker_instance.get_current_job = MagicMock(return_value=mock_job)
        mock_worker.all.return_value = [mock_worker_instance]

        ingest_activity_data()
        assert rq_queue.count == initial_job_count

    @pytest.mark.django_db
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @patch('datahub.company_activity.tasks.ingest_company_activity.Worker')
    @mock_aws
    def test_no_running_job(self, mock_worker, mock_scheduler, test_files):
        """
        Test that the check for an already running ingestion job succeeds
        when there are no jobs currently running
        """
        setup_s3_bucket(BUCKET, test_files)
        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count
        mock_worker_instance = Worker(['long-running'], connection=redis)
        mock_worker_instance.get_current_job = MagicMock(return_value=None)
        mock_worker.all.return_value = [mock_worker_instance]
        ingest_activity_data()
        assert rq_queue.count == initial_job_count + 1

    @pytest.mark.django_db
    @mock_aws
    def test_child_job(self, caplog, test_files):
        """
        Test that scheduled child job is run successfully
        """
        new_file = GREAT_PREFIX + '20240920T000000/full_ingestion.jsonl.gz'
        setup_s3_bucket(BUCKET, test_files)
        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        for file in test_files:
            if not file == new_file:
                IngestedFile.objects.create(filepath=file)

        with caplog.at_level(logging.INFO):
            ingest_activity_data()
            assert f'Ingesting file: {new_file} started' in caplog.text
