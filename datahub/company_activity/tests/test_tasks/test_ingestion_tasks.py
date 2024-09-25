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
from datahub.company_activity.tasks.ingest_company_activity import (
    BUCKET, CompanyActivityIngestionTask, GREAT_PREFIX, REGION,
)
from datahub.core.queues.constants import EVERY_TEN_MINUTES


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
    @mock_aws
    def test_ingestion_job_is_queued_for_new_files(self, test_files):
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
        initial_job_count = len(rq_queue.jobs)

        task = CompanyActivityIngestionTask()
        task.ingest_activity_data()
        assert len(rq_queue.jobs) == initial_job_count + 1
        job = rq_queue.jobs[-1]
        fn = 'datahub.company_activity.tasks.ingest_company_activity.ingest_great_data'
        assert job.func_name == fn
        assert job.args[0] == new_file
