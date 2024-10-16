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
from datahub.investment_lead.serializers import CreateEYBLeadTriageSerializer
from datahub.investment_lead.tasks.ingest_common import (
    BUCKET,
    DATE_FORMAT,
    REGION,
)
from datahub.investment_lead.tasks.ingest_eyb_triage import (
    EYBTriageDataIngestionTask,
    ingest_eyb_triage_data,
    TRIAGE_PREFIX,
)
from datahub.investment_lead.test.factories import EYBLeadFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_file():
    filepath = 'datahub/investment_lead/test/fixtures/triage.jsonl.gz'
    return open(filepath, 'rb')


@pytest.fixture
def test_file_path():
    return f'{TRIAGE_PREFIX}/20240920T000000/triage.jsonl.gz'


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


class TestEYBTriageDataIngestionTasks:
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

    def test_get_last_ingestion_datetime_of_triage_data(self):
        triage_filepath_1 = 'data-flow/eyb-triage-pipeline/1.jsonl.gz'
        triage_filepath_2 = 'data-flow/eyb-triage-pipeline/2.jsonl.gz'
        user_filepath = 'data-flow/eyb-user-pipeline/1.jsonl.gz'

        CompanyActivityIngestedFileFactory(
            filepath = triage_filepath_1,
            created_on = datetime.now() - timedelta(days=2)
        )
        most_recent_triage_file = CompanyActivityIngestedFileFactory(
            filepath = triage_filepath_2,
            created_on = datetime.now() - timedelta(days=1)
        )
        CompanyActivityIngestedFileFactory(
            filepath = user_filepath,
            created_on = datetime.now()
        )

        last_triage_ingestion_datetime = EYBTriageDataIngestionTask(
            serializer_class=CreateEYBLeadTriageSerializer,
            prefix='data-flow/eyb-triage-pipeline',
        )._last_ingestion_datetime

        assert last_triage_ingestion_datetime == most_recent_triage_file.created_on

    @mock_aws
    def test_eyb_triage_data_ingestion_updates_existing(self, test_file, test_file_path):
        """
        Test that for records which have been previously ingested, updated fields
        have their new values ingested
        """
        wales_id = constants.UKRegion.wales.value.id
        northern_ireland_id = constants.UKRegion.northern_ireland.value.id
        hashed_uuid = '4af31422fa9b28aa43fdf6b57ecf1d14be0256b657a0279cec71af10f7690be6'
        EYBLeadFactory(triage_hashed_uuid=hashed_uuid, location_id=wales_id)
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        ingest_eyb_triage_data(BUCKET, test_file_path)
        updated = EYBLead.objects.get(triage_hashed_uuid=hashed_uuid)
        assert str(updated.location.id) == northern_ireland_id

    @mock_aws
    def test_skip_unchanged_records(self, test_file_path):
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
                'modified': yesterday,
                'sector': 'Mining',
                'sectorSub': 'Mining vehicles, transport and equipment',
            },
        ), default=str)
        test_file = gzip.compress(record.encode('utf-8'))
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        ingest_eyb_triage_data(BUCKET, test_file_path)
        assert EYBLead.objects.count() == 0

    @mock_aws
    def test_invalid_file(self, test_file_path):
        """
        Test that an exception is raised when the file is not valid
        """
        setup_s3_bucket(BUCKET)
        with pytest.raises(Exception) as e:
            ingest_eyb_triage_data(BUCKET, test_file_path)
        exception = e.value.args[0]
        assert 'The specified key does not exist' in exception
        expected = f"key: '{test_file_path}'"
        assert expected in exception
