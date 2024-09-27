import boto3
import pytest

from moto import mock_aws

from datahub.company_activity.models import Great
from datahub.company_activity.tasks.ingest_company_activity import BUCKET, GREAT_PREFIX
from datahub.company_activity.tasks.ingest_great_data import (
    GreatIngestionTask, REGION,
)


@pytest.fixture
def test_file():
    filepath = 'datahub/company_activity/tests/test_tasks/fixtures/great/full_ingestion.jsonl.gz'
    return open(filepath, 'rb')


@pytest.fixture
def test_file_path():
    return GREAT_PREFIX + '20240920T000000/full_ingestion.jsonl.gz'


@mock_aws
def setup_s3_client():
    return boto3.client('s3', REGION)


@mock_aws
def setup_s3_bucket(bucket_name):
    mock_s3_client = setup_s3_client()
    mock_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': REGION},
    )


@mock_aws
def setup_s3_files(bucket_name, test_file, test_file_path):
    mock_s3_client = setup_s3_client()
    mock_s3_client.put_object(Bucket=bucket_name, Key=test_file_path, Body=test_file)


class TestGreatIngestionTasks:
    @pytest.mark.django_db
    @mock_aws
    def test_great_data_file_ingestion(self, test_file, test_file_path):
        """
        Test that a Great data file is ingested correctly
        """
        initial_great_activity_count = Great.objects.count()
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        task = GreatIngestionTask()
        task.ingest(BUCKET, test_file_path)
        assert Great.objects.count() == initial_great_activity_count + 28

    def test_invalid_file(self, test_file_path):
        """
        Test that an exception is raised when the file is not valid
        """
        setup_s3_bucket(BUCKET)
        task = GreatIngestionTask()
        with pytest.raises(Exception):
            task.ingest(BUCKET, test_file_path)
