import logging

from unittest import mock

import pytest
from moto import mock_aws

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.metadata.models import PostcodeData
from datahub.metadata.serializers import PostcodeDataSerializer
from datahub.metadata.tasks import (
    postcode_data_identification_task,
    postcode_data_ingestion_task,
    POSTCODE_DATA_PREFIX,
    PostcodeDataIngestionTask,
)
from datahub.metadata.test.factories import (
    generate_hashed_uuid,
    postcode_data_record_faker,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def postcode_object_key():
    return f'{POSTCODE_DATA_PREFIX}object.json.gz'


@mock_aws
def test_identification_task_schedules_ingestion_task(postcode_object_key, caplog):
    with (
        mock.patch('datahub.ingest.tasks.job_scheduler') as mock_scheduler,
        mock.patch.object(
            S3ObjectProcessor, 'get_most_recent_object_key', return_value=postcode_object_key,
        ),
        mock.patch.object(S3ObjectProcessor, 'has_object_been_ingested', return_value=False),
        caplog.at_level(logging.INFO),
    ):
        postcode_data_identification_task()

        assert 'Postcode data identification task started...' in caplog.text
        assert f'Scheduled ingestion of {postcode_object_key}' in caplog.text
        assert 'Postcode data identification task finished.' in caplog.text

    mock_scheduler.assert_called_once_with(
        function=postcode_data_ingestion_task,
        function_kwargs={
            'object_key': postcode_object_key,
        },
        queue_name='long-running',
        description=f'Ingest {postcode_object_key}',
    )


@mock_aws
class TestPostcodeDataIngestionTask:

    @pytest.fixture
    def ingestion_task(self, postcode_object_key):
        return PostcodeDataIngestionTask(
            object_key=postcode_object_key,
            s3_processor=S3ObjectProcessor(prefix=POSTCODE_DATA_PREFIX),
            serializer_class=PostcodeDataSerializer,
        )

    def test_get_hashed_uuid(self, ingestion_task):
        record = postcode_data_record_faker()
        assert ingestion_task._get_hashed_uuid(record) == record['hashedUuid']

    def test_process_record_creates_postcode_data_instance(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        record = postcode_data_record_faker({'hashed_uuid': hashed_uuid})
        ingestion_task._process_record(record)

        assert len(ingestion_task.created_ids) == 1
        assert len(ingestion_task.updated_ids) == 0
        assert len(ingestion_task.errors) == 0
        assert PostcodeData.objects.filter(hashed_uuid=hashed_uuid).exists()
