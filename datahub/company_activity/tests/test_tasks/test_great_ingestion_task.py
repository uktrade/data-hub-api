import json

import boto3
import pytest

from moto import mock_aws
from sentry_sdk import init
from sentry_sdk.transport import Transport

from datahub.company_activity.models import Great, IngestedFile
from datahub.company_activity.tasks.ingest_company_activity import BUCKET, GREAT_PREFIX
from datahub.company_activity.tasks.ingest_great_data import (
    GreatIngestionTask, REGION,
)
from datahub.company_activity.tests.factories import CompanyActivityGreatFactory
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
    def test_great_data_file_ingestion(self, test_file, test_file_path):
        """
        Test that a Great data file is ingested correctly and the ingested file
        is added to the IngestedFile table
        """
        initial_great_activity_count = Great.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        task = GreatIngestionTask()
        task.ingest(BUCKET, test_file_path)
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
        CompanyActivityGreatFactory(data_country=country)
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        task = GreatIngestionTask()
        task.ingest(BUCKET, test_file_path)
        updated = Great.objects.get(form_id='dit:directoryFormsApi:Submission:9034')
        assert str(updated.data_country_id) == '876a9ab2-5d95-e211-a939-e4115bead28a'
        assert updated.actor_dit_is_blacklisted is False
        assert updated.actor_dit_is_whitelisted is True
        assert updated.data_full_name == 'Keith Duncan'

    @mock_aws
    def test_invalid_file(self, test_file_path):
        """
        Test that an exception is raised when the file is not valid
        """
        mock_transport = MockSentryTransport()
        init(transport=mock_transport)
        setup_s3_bucket(BUCKET)
        task = GreatIngestionTask()
        with pytest.raises(Exception) as e:
            task.ingest(BUCKET, test_file_path)
        exception = e.value.args[0]
        assert 'The specified key does not exist' in exception
        expected = " key: 'data-flow/exports/GreatGovUKFormsPipeline/" \
            '20240920T000000/full_ingestion.jsonl.gz'
        assert expected in exception

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
                    "attributedTo": {
                      "type": "dit:directoryFormsApi:SubmissionAction:gov-notify-email",
                      "id": "dit:directoryFormsApi:SubmissionType:export-support-service"
                    },
                    "url": "https://kane.net/",
                    "dit:directoryFormsApi:Submission:Meta": {
                      "action_name": "gov-notify-email",
                      "template_id": "76f12003-74e8-4e6b-bbe9-8edc1b8619ae",
                      "email_address": "brownalexandra@example.com"
                    },
                    "dit:directoryFormsApi:Submission:Data": {
                      "comment": "Issue why why morning save parent southern.",
                      "country": "ZZ",
                      "full_name": "Tina Gray",
                      "website_url": "https://www.henderson-thomas.info/",
                      "company_name": "Foster, Murphy and Diaz",
                      "company_size": "1 - 10",
                      "phone_number": "12345678",
                      "terms_agreed": true,
                      "email_address": "ericwilliams@example.com",
                      "opportunities": ["https://white.net/app/tagscategory.php"],
                      "role_in_company": "test",
                      "opportunity_urls": "https://www.brown-andrade.com/wp-content/tagfaq.htm"
                    }
                },
                "actor": {
                    "type": "dit:directoryFormsApi:Submission:Sender",
                    "id": "dit:directoryFormsApi:Sender:1041",
                    "dit:emailAddress": "crystalbrock@example.org",
                    "dit:isBlacklisted": true,
                    "dit:isWhitelisted": false,
                    "dit:blackListedReason": null
                }
        }
        """
        mock_transport = MockSentryTransport()
        init(transport=mock_transport)
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = Great.objects.get(form_id='dit:directoryFormsApi:Submission:5249')
        assert result.data_country is None
        sentry_event = mock_transport.events[0].get_event()
        expected_message = 'Could not match country with iso code: ZZ, ' + \
            'for form: dit:directoryFormsApi:Submission:5249'
        assert sentry_event['logentry']['message'] == expected_message
