import importlib
import sys

from unittest.mock import patch

import boto3
import pytest

from django.conf import settings
from moto import mock_aws

from redis import Redis
from rq_scheduler import Scheduler

from datahub.company_activity.tasks.ingest_company_activity import (
    CompanyActivityIngestionTask, GREAT_PREFIX, REGION,
)
from datahub.core.queues.constants import EVERY_TEN_MINUTES


@pytest.fixture
def bucket_name():
    return 'mock-bucket'


@mock_aws
def setup_s3_bucket(bucket_name):
    mock_s3_client = boto3.client('s3', REGION)
    mock_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': REGION},
    )
    filename = GREAT_PREFIX + 'full_ingestion.jsonl.gz'
    mock_s3_client.put_object(Bucket=bucket_name, Key=filename, Body='Test contents')


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
    def test_listing_great_data_files(self, bucket_name):
        """
        Test retrieval of the latest Great data file from S3
        """
        setup_s3_bucket(bucket_name)
        task = CompanyActivityIngestionTask()
        objects = task.list_objects(bucket_name, GREAT_PREFIX)
        expected_file = GREAT_PREFIX + 'full_ingestion.jsonl.gz'
        assert objects == [expected_file]
