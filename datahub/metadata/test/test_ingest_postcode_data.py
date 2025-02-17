import logging

from unittest import mock

import pytest
from moto import mock_aws

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.metadata.tasks import (
    postcode_data_identification_task,
    postcode_data_ingestion_task,
    POSTCODE_DATA_PREFIX,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def postcode_object_key():
    return f'{POSTCODE_DATA_PREFIX}object.json.gz'


@mock_aws
def test_identification_task_schedules_ingestion_task(self, postcode_object_key, caplog):
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
        assert 'Postcode identification task finished.' in caplog.text

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
    pass
