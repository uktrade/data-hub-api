import logging

import boto3
import pytest

from moto import mock_aws

from datahub.company_activity.models import IngestedFile
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.tasks.ingest_eyb_triage import (
    BUCKET,
    ingest_eyb_triage_data,
    REGION,
    TRIAGE_PREFIX,
)


@pytest.fixture
def test_file():
    filepath = 'datahub/investment_lead/test/fixtures/full_ingestion.jsonl.gz'
    return open(filepath, 'rb')


@pytest.fixture
def test_file_path():
    return f'{TRIAGE_PREFIX}/20240920T000000/full_ingestion.jsonl.gz'


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
    def test_eyb_triage_file_ingestion(self, caplog, test_file, test_file_path):
        """
        Test that a EYB triage data file is ingested correctly and the ingested
        file is added to the IngestedFile table
        """
        initial_eyb_lead_count = EYBLead.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        with caplog.at_level(logging.INFO):
            ingest_eyb_triage_data(BUCKET, test_file_path)
            assert f'Ingesting file: {test_file_path} started' in caplog.text
            assert f'Ingesting file: {test_file_path} finished' in caplog.text
        assert EYBLead.objects.count() > initial_eyb_lead_count
        assert IngestedFile.objects.count() == initial_ingested_count + 1
