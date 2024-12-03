import gzip
import json
import logging

import boto3
import pytest

from moto import mock_aws
from sentry_sdk import init
from sentry_sdk.transport import Transport

from datahub.company_activity.models import StovaEvent, IngestedFile
from datahub.company_activity.tasks.constants import BUCKET, GREAT_PREFIX, REGION
from datahub.company_activity.tasks.ingest_stova_events import (
    ingest_stova_data,
)
from datahub.company_activity.tests.factories import (
    StovaEventFactory,
)


@pytest.fixture
def test_file():
    filepath = (
        'datahub/company_activity/tests/test_tasks/fixtures/great/stova/stovaEventFake.jsonl.gz'
    )
    return open(filepath, 'rb')


@pytest.fixture
def test_file_path():
    return f'{GREAT_PREFIX}20240920T000000.jsonl.gz'


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


class MockSentryTransport(Transport):
    def __init__(self):
        self.events = []

    def capture_event(self, event):
        pass

    def capture_envelope(self, envelope):
        self.events.append(envelope)


class TestStovaIngestionTasks:
    @pytest.mark.django_db
    @mock_aws
    def test_stova_data_file_ingestion(self, caplog, test_file, test_file_path):
        """
        Test that a Aventri/Stova data file is ingested correctly and the ingested file
        is added to the IngestedFile table
        """
        initial_stova_activity_count = StovaEvent.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        with caplog.at_level(logging.INFO):
            ingest_stova_data(BUCKET, test_file_path)
            assert f'Ingesting file: {test_file_path} started' in caplog.text
            assert f'Ingesting file: {test_file_path} finished' in caplog.text
        assert StovaEvent.objects.count() == initial_stova_activity_count + 4
        assert IngestedFile.objects.count() == initial_ingested_count + 1

    @pytest.mark.django_db
    @mock_aws
    def test_skip_previously_ingested_records(self, test_file_path):
        """
        Test that we skip updating records that have already been ingested
        """
        StovaEventFactory(event_id=123456789)
        record = json.dumps(
            dict(
                {
                    'id': '123456789',
                    'created_at': '2024-09-19T14:00:34.069',
                }
            ),
            default=str,
        )
        test_file = gzip.compress(record.encode('utf-8'))
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        ingest_stova_data(BUCKET, test_file_path)
        assert StovaEvent.objects.filter(event_id=123456789).count() == 1

    @pytest.mark.django_db
    @mock_aws
    def test_invalid_file(self, test_file_path):
        """
        Test that an exception is raised when the file is not valid
        """
        mock_transport = MockSentryTransport()
        init(transport=mock_transport)
        setup_s3_bucket(BUCKET)
        with pytest.raises(Exception) as e:
            ingest_stova_data(BUCKET, test_file_path)
        exception = e.value.args[0]
        assert 'The specified key does not exist' in exception
        expected = " key: 'data-flow/exports/ExportAventriEvents//" '20240920T000000.jsonl.gz'
        assert expected in exception
