import gzip
import json
import logging

from datetime import datetime, timedelta

import boto3
import pytest

from moto import mock_aws
from sentry_sdk import init
from sentry_sdk.transport import Transport

from datahub.company_activity.models import Great, IngestedFile
from datahub.company_activity.tasks.ingest_company_activity import BUCKET, GREAT_PREFIX
from datahub.company_activity.tasks.ingest_great_data import (
    DATE_FORMAT, GreatIngestionTask, ingest_great_data, REGION,
)
from datahub.company_activity.tests.factories import (
    CompanyActivityGreatFactory,
    CompanyActivityIngestedFileFactory,
)
from datahub.metadata.models import Country


@pytest.fixture
def test_file():
    filepath = 'datahub/company_activity/tests/test_tasks/fixtures/great/full_ingestion.jsonl.gz'
    return open(filepath, 'rb')


@pytest.fixture
def test_file_path():
    return f'{GREAT_PREFIX}20240920T000000/full_ingestion.jsonl.gz'


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


class TestGreatIngestionTasks:
    @pytest.mark.django_db
    @mock_aws
    def test_great_data_file_ingestion(self, caplog, test_file, test_file_path):
        """
        Test that a Great data file is ingested correctly and the ingested file
        is added to the IngestedFile table
        """
        initial_great_activity_count = Great.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        with caplog.at_level(logging.INFO):
            ingest_great_data(BUCKET, test_file_path)
            assert f'Ingesting file: {test_file_path} started' in caplog.text
            assert f'Ingesting file: {test_file_path} finished' in caplog.text
        assert Great.objects.count() == initial_great_activity_count + 28
        assert IngestedFile.objects.count() == initial_ingested_count + 1

    @pytest.mark.django_db
    @mock_aws
    def test_great_data_ingestion_updates_existing(self, test_file, test_file_path):
        """
        Test that for records which have been previously ingested, updated fields
        have their new values ingested
        """
        country = Country.objects.get(id='0350bdb8-5d95-e211-a939-e4115bead28a')
        CompanyActivityGreatFactory(form_id='9034', data_country=country)
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        ingest_great_data(BUCKET, test_file_path)
        updated = Great.objects.get(form_id='9034')
        assert str(updated.data_country_id) == '876a9ab2-5d95-e211-a939-e4115bead28a'
        assert updated.actor_dit_is_blacklisted is False
        assert updated.actor_dit_is_whitelisted is True
        assert updated.data_full_name == 'Keith Duncan'

    @pytest.mark.django_db
    @mock_aws
    def test_skip_unchanged_records(self, test_file_path):
        """
        Test that we skip updating records whose published date is older than the last
        file ingestion date
        """
        yesterday = datetime.strftime(datetime.now() - timedelta(1), DATE_FORMAT)
        CompanyActivityIngestedFileFactory(created_on=datetime.now())
        record = json.dumps(dict(
            object={
                'id': 'dit:directoryFormsApi:Submission:5249',
                'published': yesterday,
                'attributedTo': {
                    'type': 'dit:directoryFormsApi:SubmissionAction:gov-notify-email',
                    'id': 'dit:directoryFormsApi:SubmissionType:export-support-service',
                },
            },
        ), default=str)
        test_file = gzip.compress(record.encode('utf-8'))
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        ingest_great_data(BUCKET, test_file_path)
        assert Great.objects.count() == 0

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
            ingest_great_data(BUCKET, test_file_path)
        exception = e.value.args[0]
        assert 'The specified key does not exist' in exception
        expected = " key: 'data-flow/exports/GreatGovUKFormsPipeline/" \
            '20240920T000000/full_ingestion.jsonl.gz'
        assert expected in exception

    @pytest.mark.django_db
    def test_country_code_is_country_name(self):
        """
        Test that when the country code is a country name string instead
        of an iso code, we are able to lookup `country` case-insensitively
        and regardless of whitespacing
        """
        data = """
            {
                "object": {
                    "id": "dit:directoryFormsApi:Submission:5249",
                    "published": "2024-09-19T14:00:34.069Z",
                    "dit:directoryFormsApi:Submission:Data": {
                     "country": "South  AfRica "
                    }
                }
            }
        """
        initial_count = Great.objects.count()
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        assert Great.objects.count() == initial_count + 1
        result = Great.objects.get(form_id='5249')
        assert result.data_country.iso_alpha2_code == 'ZA'

    @pytest.mark.django_db
    def test_invalid_country_code(self):
        """
        Test that when the country code provided in the data file cannot be found
        in the metadata countries table, we save the record with data_country: None
        and trigger a Sentry alert
        """
        data = """
            {
                "object": {
                    "id": "dit:directoryFormsApi:Submission:5249",
                    "published": "2024-09-19T14:00:34.069Z",
                    "dit:directoryFormsApi:Submission:Data": {
                     "country": "ZZ"
                    }
                }
            }
        """
        mock_transport = MockSentryTransport()
        init(transport=mock_transport)
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = Great.objects.get(form_id='5249')
        assert result.data_country is None
        sentry_event = mock_transport.events[0].get_event()
        expected_message = 'Could not match country with iso code: ZZ, ' + \
            'for form: 5249'
        assert sentry_event['logentry']['message'] == expected_message

    @pytest.mark.django_db
    @mock_aws
    def test_null_url(self, test_file_path):
        """
        Test that we can ingest records with URL field null
        """
        initial_count = Great.objects.count()
        data = """
            {
                "object": {
                    "id": "dit:directoryFormsApi:Submission:5249",
                    "published": "2024-09-19T14:00:34.069Z",
                    "url": null
                }
            }
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        assert Great.objects.count() == initial_count + 1
        data = """
            {
                "object": {
                    "id": "dit:directoryFormsApi:Submission:5250",
                    "published": "2024-09-19T15:00:34.069Z"
                }
            }
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        assert Great.objects.count() == initial_count + 2

    @pytest.mark.django_db
    @mock_aws
    def test_long_field_values(self, test_file_path):
        """
        Test that we can ingest records with long field values
        """
        initial_count = Great.objects.count()
        long_text = (
            'Some text string that is longer than 255 characters.'
            'Testing that because our default Char field storage is'
            'limited to 255 chars so fields with values longer than'
            'that either need to be stored as TextFields if we need'
            'the full value or truncated if we do not. Long long long.'
        )
        data = f"""
            {{
                "object": {{
                    "id": "dit:directoryFormsApi:Submission:5249",
                    "published": "2024-09-19T14:00:34.069Z",
                    "url": "{long_text}",
                    "dit:directoryFormsApi:Submission:Data": {{
                        "comment": "{long_text}",
                        "opportunity_urls": "{long_text}",
                        "full_name": "{long_text}",
                        "website_url": "{long_text}",
                        "company_name": "{long_text}",
                        "company_size": "{long_text}",
                        "phone_number": "{long_text}",
                        "email_address": "{long_text}",
                        "role_in_company": "{long_text}"
                    }}
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        assert Great.objects.count() == initial_count + 1
