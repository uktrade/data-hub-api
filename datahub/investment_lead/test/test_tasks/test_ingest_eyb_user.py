import logging

from datetime import datetime, timedelta

import boto3
import pytest

from datahub.investment_lead.serializers import CreateEYBLeadUserSerializer
from moto import mock_aws

from datahub.company_activity.models import IngestedFile
from datahub.company_activity.tests.factories import CompanyActivityIngestedFileFactory
from datahub.core import constants
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.tasks.ingest_common import (
    BUCKET,
    DATE_FORMAT,
    REGION,
)
from datahub.investment_lead.tasks.ingest_eyb_user import (
    EYBUserDataIngestionTask,
    ingest_eyb_user_data,
    USER_PREFIX,
)
from datahub.investment_lead.test.factories import (
    create_fake_file,
    eyb_lead_user_record_faker,
    EYBLeadFactory,
    generate_hashed_uuid,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_file_path():
    return f'{USER_PREFIX}/user.jsonl.gz'


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
def setup_s3_files(bucket_name, test_file_path, test_file):
    mock_s3_client = setup_s3_client()
    mock_s3_client.put_object(Bucket=bucket_name, Key=test_file_path, Body=test_file)


class TestEYBUserDataIngestionTasks:
    @mock_aws
    def test_eyb_user_file_ingestion(self, caplog, test_file_path):
        """
        Test that a EYB user data file is ingested correctly and the ingested
        file is added to the IngestedFile table
        """
        initial_eyb_lead_count = EYBLead.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file_path, create_fake_file([eyb_lead_user_record_faker()]))
        with caplog.at_level(logging.INFO):
            ingest_eyb_user_data(BUCKET, test_file_path)
            assert f'Ingesting file: {test_file_path} started' in caplog.text
            assert f'Ingesting file: {test_file_path} finished' in caplog.text
        assert EYBLead.objects.count() > initial_eyb_lead_count
        assert IngestedFile.objects.count() == initial_ingested_count + 1

    # TODO: Fix test - created_on is being overwritten with time now so test always passes
    def test_get_last_ingestion_datetime_of_user_data(self):
        """
        Test that the most recent user data file is ingested, even when there are
        more recent files of a different data set present e.g. triage data
        """
        user_filepath_1 = 'data-flow/eyb-user-pipeline/1.jsonl.gz'
        user_filepath_2 = 'data-flow/eyb-user-pipeline/2.jsonl.gz'
        triage_filepath = 'data-flow/eyb-triage-pipeline/1.jsonl.gz'

        today = datetime.now()
        yesterday = datetime.now() - timedelta(days=1)
        two_days_ago = datetime.now() - timedelta(days=2)

        CompanyActivityIngestedFileFactory(
            filepath=user_filepath_1,
            created_on=two_days_ago,
        )
        most_recent_user_file = CompanyActivityIngestedFileFactory(
            filepath=user_filepath_2,
            created_on=yesterday,
        )
        CompanyActivityIngestedFileFactory(
            filepath=triage_filepath,
            created_on=today,
        )

        last_user_ingestion_datetime = EYBUserDataIngestionTask(
            serializer_class=CreateEYBLeadUserSerializer,
            prefix='data-flow/eyb-user-pipeline',
        )._last_ingestion_datetime

        assert last_user_ingestion_datetime == most_recent_user_file.created_on

    @mock_aws
    def test_eyb_user_data_ingestion_updates_existing(self, test_file_path):
        """
        Test that for records which have been previously ingested, updated fields
        have their new values ingested
        """
        united_kingdom_id = constants.Country.united_kingdom.value.id
        hashed_uuid = generate_hashed_uuid()
        EYBLeadFactory(user_hashed_uuid=hashed_uuid, address_country_id=united_kingdom_id)
        setup_s3_bucket(BUCKET)
        records = [
            eyb_lead_user_record_faker({
                'hashedUuid': hashed_uuid,
                'companyLocation': 'FR',
            }),
        ]
        file = create_fake_file(records)
        setup_s3_files(BUCKET, test_file_path, file)
        ingest_eyb_user_data(BUCKET, test_file_path)
        updated = EYBLead.objects.get(user_hashed_uuid=hashed_uuid)
        assert str(updated.address_country.id) == constants.Country.france.value.id

    @mock_aws
    def test_skip_unchanged_records(self, test_file_path, faker):
        """
        Test that we skip updating records whose modified date is older than the last
        file ingestion date
        """
        hashed_uuid = 'a601a725d40884114408eb1c357993b0b9a61fb58faddd271e3aac3802e71a47'
        yesterday = datetime.strftime(datetime.now() - timedelta(1), DATE_FORMAT)
        CompanyActivityIngestedFileFactory(created_on=datetime.now(), filepath=test_file_path)
        records = [
            {
                'hashedUuid': hashed_uuid,
                'created': yesterday,
                'modified': yesterday,
                'companyName': faker.company(),
                'addressLine1': faker.street_address(),
                'town': faker.city(),
                'companyLocation': faker.country_code(),
                'fullName': faker.name(),
                'email': faker.email(),
            },
        ]
        file = create_fake_file(records)
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file_path, file)
        ingest_eyb_user_data(BUCKET, test_file_path)
        assert EYBLead.objects.count() == 0

    @mock_aws
    def test_invalid_file(self, test_file_path):
        """
        Test that an exception is raised when the file is not valid
        """
        setup_s3_bucket(BUCKET)
        with pytest.raises(Exception) as e:
            ingest_eyb_user_data(BUCKET, test_file_path)
        exception = e.value.args[0]
        assert 'The specified key does not exist' in exception
        expected = f"key: '{test_file_path}'"
        assert expected in exception
