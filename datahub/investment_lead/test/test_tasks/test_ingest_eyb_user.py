import gzip
import json
import logging

from datetime import datetime, timedelta

import boto3
import pytest

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
    ingest_eyb_user_data,
    USER_PREFIX,
)
from datahub.investment_lead.test.factories import EYBLeadFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_file():
    filepath = 'datahub/investment_lead/test/fixtures/user.jsonl.gz'
    return open(filepath, 'rb')


@pytest.fixture
def test_file_path():
    return f'{USER_PREFIX}/20240920T000000/user.jsonl.gz'


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


class TestEYBUserDataIngestionTasks:
    @mock_aws
    def test_eyb_user_file_ingestion(self, caplog, test_file, test_file_path):
        """
        Test that a EYB user data file is ingested correctly and the ingested
        file is added to the IngestedFile table
        """
        initial_eyb_lead_count = EYBLead.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        with caplog.at_level(logging.INFO):
            ingest_eyb_user_data(BUCKET, test_file_path)
            assert f'Ingesting file: {test_file_path} started' in caplog.text
            assert f'Ingesting file: {test_file_path} finished' in caplog.text
        assert EYBLead.objects.count() > initial_eyb_lead_count
        assert IngestedFile.objects.count() == initial_ingested_count + 1

    @mock_aws
    def test_eyb_user_data_ingestion_updates_existing(self, test_file, test_file_path):
        """
        Test that for records which have been previously ingested, updated fields
        have their new values ingested
        """
        united_kingdom_id = constants.Country.united_kingdom.value.id
        france_id = constants.Country.france.value.id
        # This uuid is from a record in the fixture data, which has companyLocation='FR'
        hashed_uuid = '9cdd98d35e27101f0e0c3ab14ff58b59c21e66076b77b9683ece4342311bed7e'
        EYBLeadFactory(user_hashed_uuid=hashed_uuid, address_country_id=united_kingdom_id)
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        ingest_eyb_user_data(BUCKET, test_file_path)
        updated = EYBLead.objects.get(user_hashed_uuid=hashed_uuid)
        assert str(updated.address_country.id) == france_id

    @mock_aws
    def test_skip_unchanged_records(self, faker, test_file_path):
        """
        Test that we skip updating records whose modified date is older than the last
        file ingestion date
        """
        hashed_uuid = 'a601a725d40884114408eb1c357993b0b9a61fb58faddd271e3aac3802e71a47'
        yesterday = datetime.strftime(datetime.now() - timedelta(1), DATE_FORMAT)
        CompanyActivityIngestedFileFactory(created_on=datetime.now())
        record = json.dumps(dict(
            object={
                'hashedUuid': hashed_uuid,
                'created': yesterday,
                'modified': yesterday,  # This field
                'companyName': faker.company(),
                'addressLine1': faker.street_address(),
                'town': faker.city(),
                'companyLocation': faker.country_code(),
                'fullName': faker.name(),
                'email': faker.email(),
            },
        ), default=str)
        test_file = gzip.compress(record.encode('utf-8'))
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
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
