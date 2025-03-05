import logging
from decimal import Decimal

from unittest import mock

import boto3
import pytest

from moto import mock_aws
from sentry_sdk import init
from sentry_sdk.transport import Transport

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.constants import (
    AWS_REGION,
    S3_BUCKET_NAME,
)
from datahub.metadata.models import (
    PostcodeData,
)
from datahub.metadata.tasks import (
    postcode_data_identification_task,
    postcode_data_ingestion_task,
    POSTCODE_DATA_PREFIX,
)
from datahub.metadata.test.factories import (
    PostcodeDataFactory,
)


@pytest.fixture
def test_file_path():
    return f'{POSTCODE_DATA_PREFIX}object.json.gz'


@pytest.fixture
def test_file():
    filepath = (
        'datahub/metadata/test/fixtures/postcodes.json.gz'
    )
    return open(filepath, 'rb')


@mock_aws
def setup_s3_client():
    return boto3.client('s3', AWS_REGION)


@mock_aws
def setup_s3_bucket(bucket_name):
    mock_s3_client = setup_s3_client()
    mock_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': AWS_REGION},
    )


class MockSentryTransport(Transport):
    def __init__(self):
        self.events = []

    def capture_event(self, event):
        pass

    def capture_envelope(self, envelope):
        self.events.append(envelope)


@mock_aws
def setup_s3_files(bucket_name, test_file, test_file_path):
    mock_s3_client = setup_s3_client()
    mock_s3_client.put_object(Bucket=bucket_name, Key=test_file_path, Body=test_file)


@mock_aws
def test_identification_task_schedules_ingestion_task(test_file_path, caplog):
    with (
        mock.patch('datahub.ingest.tasks.job_scheduler') as mock_scheduler,
        mock.patch.object(
            S3ObjectProcessor, 'get_most_recent_object_key', return_value=test_file_path,
        ),
        mock.patch.object(S3ObjectProcessor, 'has_object_been_ingested', return_value=False),
        caplog.at_level(logging.INFO),
    ):
        postcode_data_identification_task()

        assert 'Postcode data identification task started...' in caplog.text
        assert f'Scheduled ingestion of {test_file_path}' in caplog.text
        assert 'Postcode data identification task finished.' in caplog.text

    mock_scheduler.assert_called_once_with(
        function=postcode_data_ingestion_task,
        function_kwargs={
            'object_key': test_file_path,
        },
        queue_name='long-running',
        description=f'Ingest {test_file_path}',
    )


class TestPostcodeDataIngestionTask:
    @pytest.mark.django_db
    @mock_aws
    def test_ingesting_postcodes(self, test_file_path, test_file):
        """
        Test that when given a postcode file, the task inserts new records,
        updates the field values of existing records, and deletes records
        that exist in the database but not in the file.
        """
        PostcodeDataFactory(id=400859, region_name='South West', lat=44.244941)
        PostcodeDataFactory(id=999999999)
        initial_postcode_ids = PostcodeData.objects.values_list('id', flat=True)
        assert set(initial_postcode_ids) == set([400859, 999999999])
        setup_s3_bucket(S3_BUCKET_NAME)
        setup_s3_files(S3_BUCKET_NAME, test_file, test_file_path)
        postcode_data_ingestion_task(test_file_path)
        result_postcode_ids = PostcodeData.objects.values_list('id', flat=True)
        assert set(result_postcode_ids) == set([2656, 8661, 400858, 400859, 426702])
        updated_postcode = PostcodeData.objects.get(id=400859)
        expected_region = 'East of England'
        expected_lat = Decimal('52.244847')
        assert (updated_postcode.region_name) == expected_region
        assert (updated_postcode.lat) == expected_lat

    @pytest.mark.django_db
    @mock_aws
    def test_invalid_file(self, test_file_path):
        """
        Test that an exception is raised when the file is not valid
        """
        mock_transport = MockSentryTransport()
        init(transport=mock_transport)
        setup_s3_bucket(S3_BUCKET_NAME)
        with pytest.raises(Exception) as e:
            postcode_data_ingestion_task(test_file_path)
        exception = e.value.args[0]
        assert" key: 'data-flow/exports/ExportPostcodeDirectory/object.json.gz" in exception
