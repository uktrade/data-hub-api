import boto3
import pytest

from moto import mock_aws

# from datahub.company_activity.models import IngestedFile
from datahub.company_activity.tasks.ingest_company_activity import GREAT_PREFIX
from datahub.company_activity.tasks.ingest_great_data import (
    BUCKET, GreatIngestionTask, REGION,
)


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


class TestGreatIngestionTasks:
    @pytest.mark.django_db
    @mock_aws
    def test_great_data_file_ingestion(self, test_files):
        """
        Test that a Great data file is ingested correctly
        """
        new_file = GREAT_PREFIX + '20240920T000000/full_ingestion.jsonl.gz'
        setup_s3_bucket(BUCKET, test_files)
        task = GreatIngestionTask()
        task.ingest(new_file)
