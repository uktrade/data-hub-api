import gzip
import json
import logging

from datetime import datetime

import boto3
import pytest

from moto import mock_aws
from sentry_sdk import init
from sentry_sdk.transport import Transport

from datahub.company_activity.models import IngestedFile, StovaEvent
from datahub.company_activity.tasks.constants import BUCKET, REGION, STOVA_EVENT_PREFIX
from datahub.company_activity.tasks.ingest_stova_events import (
    ingest_stova_data,
    StovaEventIngestionTask,
)
from datahub.company_activity.tests.factories import (
    StovaEventFactory,
)


@pytest.fixture
def test_file():
    filepath = (
        'datahub/company_activity/tests/test_tasks/fixtures/stova/stovaEventFake2.jsonl.gz'
    )
    return open(filepath, 'rb')


@pytest.fixture
def test_file_path():
    return f'{STOVA_EVENT_PREFIX}stovaEventFake2.jsonl.gz'


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
        assert StovaEvent.objects.count() == initial_stova_activity_count + 27
        assert IngestedFile.objects.count() == initial_ingested_count + 1

    @pytest.mark.django_db
    @mock_aws
    def test_skip_previously_ingested_records(self, test_file_path):
        """
        Test that we skip updating records that have already been ingested
        """
        StovaEventFactory(stova_event_id=123456789)
        record = json.dumps(
            dict(
                {
                    'id': 123456789,
                    'created_at': '2024-09-19T14:00:34.069',
                },
            ),
            default=str,
        )
        test_file = gzip.compress(record.encode('utf-8'))
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        ingest_stova_data(BUCKET, test_file_path)
        assert StovaEvent.objects.filter(stova_event_id=123456789).count() == 1

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
        expected = "key: 'data-flow/exports/ExportAventriEvents/" 'stovaEventFake2.jsonl.gz'
        assert expected in exception

    @pytest.mark.django_db
    def test_stova_event_fields_are_saved(self):
        """
        Test that the ingested stova event fields are saved to the StovaEvent model.
        """
        data = {
            'id': 2367,
            'url': 'https://simmons.net/',
            'city': 'Lake William',
            'code': '12345',
            'name': 'why',
            'state': 'Montana',
            'country': 'Canada',
            'max_reg': 1561,
            'end_date': '2024-10-08 10:48:36.204478+00:00',
            'timezone': 'America/Grenada',
            'folder_id': 3479,
            'live_date': '2024-10-08 10:48:36.204549+00:00',
            'close_date': '2024-10-08 10:48:36.204570+00:00',
            'created_by': 5808,
            'price_type': 'net',
            'start_date': '2024-10-08 10:48:36.204592+00:00',
            'description': 'star',
            'modified_by': 9588,
            'contact_info': 'molinakaren@example.com',
            'created_date': '2024-10-08 10:48:36.204839+00:00',
            'location_city': 'Port Laurenside',
            'location_name': '271 Carlos Key\nWest Sarah WV 98592',
            'modified_date': '2024-10-08 10:48:36.205154+00:00',
            'client_contact': 3174,
            'location_state': 'Arkansas',
            'default_language': 'sa',
            'location_country': 'United States Minor Outlying Islands',
            'approval_required': True,
            'location_address1': '61797 Mikayla Crossing',
            'location_address2': '45871 Burke Lock',
            'location_address3': '47683 Schmidt Club Suite 021',
            'location_postcode': '85054',
            'standard_currency': 'MNT',
        }
        task = StovaEventIngestionTask()
        task.json_to_model(data)
        result = StovaEvent.objects.get(stova_event_id=2367)

        data.pop('id')
        for field, file_value in data.items():
            model_value = getattr(result, field)

            if type(model_value) is datetime:
                assert str(model_value) == file_value
                continue

            assert model_value == file_value
