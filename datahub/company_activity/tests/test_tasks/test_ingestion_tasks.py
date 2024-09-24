import importlib
import sys

from unittest.mock import patch

import boto3
import pytest

from django.conf import settings
from moto import mock_aws

from redis import Redis
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

    @mock_aws
    def test_get_most_recent_obj(self, test_files):
        """
        Test retrieval of the latest Great data file from S3
        """
        setup_s3_bucket(BUCKET, test_files)
        task = CompanyActivityIngestionTask()
        most_recent = task.get_most_recent_obj(BUCKET, GREAT_PREFIX)
        assert most_recent == GREAT_PREFIX + '20240920T000000/full_ingestion.jsonl.gz'

    @pytest.mark.django_db
    def test_file_already_ingested(self):
        """
        Test checking whether the latest file has already been ingested
        """
        task = CompanyActivityIngestionTask()
        ingested_file = GREAT_PREFIX + '20240920T000000/full_ingestion.jsonl.gz'
        not_ingested_file = GREAT_PREFIX + '20240921T000000/full_ingestion.jsonl.gz'
        IngestedFile.objects.create(filepath=ingested_file)
        result = task.has_file_been_ingested(ingested_file)
        assert result
        result = task.has_file_been_ingested(not_ingested_file)
        assert not result
