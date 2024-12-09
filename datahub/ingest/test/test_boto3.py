from datetime import (
    datetime,
    timedelta,
    timezone,
)
from unittest import mock

import pytest

from botocore.exceptions import ClientError
from django.test import override_settings
from freezegun import freeze_time
from moto import mock_aws

from datahub.ingest.boto3 import get_s3_client
from datahub.ingest.constants import (
    TEST_AWS_REGION,
    TEST_OBJECT_KEY,
    TEST_PREFIX,
)
from datahub.ingest.test.factories import IngestedObjectFactory
from datahub.ingest.utils import (
    compressed_json_faker,
    upload_objects_to_s3,
)


pytestmark = pytest.mark.django_db


class TestGetS3Client:

    def test_get_s3_client_returns_boto3_instance(self):
        with mock.patch('datahub.ingest.boto3.boto3.client') as patched_s3_client:
            get_s3_client(TEST_AWS_REGION)
            patched_s3_client.assert_called_with('s3', TEST_AWS_REGION)

    @override_settings(S3_LOCAL_ENDPOINT_URL='http://localstack')
    def test_get_s3_client_returns_local_instance(self):
        with mock.patch('datahub.ingest.boto3.boto3.client') as patched_s3_client:
            get_s3_client(TEST_AWS_REGION)
            patched_s3_client.assert_called_with(
                's3', TEST_AWS_REGION, endpoint_url='http://localstack',
            )


@mock_aws
class TestS3ObjectProcessor:

    def test_list_objects_empty_with_no_objects_in_bucket(self, s3_object_processor):
        objects = s3_object_processor.list_objects()
        assert objects == []

    def test_list_objects_with_objects_in_bucket(self, s3_object_processor, test_object_tuples):
        upload_objects_to_s3(s3_object_processor, test_object_tuples)
        objects = s3_object_processor.list_objects()
        assert len(objects) == 3
        assert all(key.startswith(TEST_PREFIX) for key in objects)
        assert all(key.endswith('.jsonl.gz') for key in objects)

    def test_get_most_recent_object(self, s3_object_processor, test_object_tuples):
        upload_objects_to_s3(s3_object_processor, test_object_tuples)
        most_recent_object = s3_object_processor.get_most_recent_object()
        assert most_recent_object == f'{TEST_PREFIX}file_c.jsonl.gz'

    def test_get_most_recent_object_when_empty(self, s3_object_processor):
        most_recent_object = s3_object_processor.get_most_recent_object()
        assert most_recent_object is None

    def test_get_object_last_modified_datetime(self, s3_object_processor):
        object_definition = (
            TEST_OBJECT_KEY, compressed_json_faker([{'test': 'content'}]),
        )
        last_modified_datetime = datetime(2024, 11, 24, 10, 00, 00, tzinfo=timezone.utc)
        with freeze_time(last_modified_datetime):
            upload_objects_to_s3(s3_object_processor, [object_definition])
        assert s3_object_processor.get_object_last_modified_datetime(TEST_OBJECT_KEY) \
            == last_modified_datetime

    def test_get_object_last_modified_datetime_raises_error(self, s3_object_processor, caplog):
        with pytest.raises(ClientError):
            s3_object_processor.get_object_last_modified_datetime(TEST_OBJECT_KEY)
        assert f'Error getting last modified datetime for {TEST_OBJECT_KEY}' in caplog.text
        assert 'NoSuchKey' in caplog.text

    def test_has_object_been_ingested_returns_true(self, s3_object_processor):
        IngestedObjectFactory(object_key=TEST_OBJECT_KEY)
        assert s3_object_processor.has_object_been_ingested(TEST_OBJECT_KEY)

    def test_has_object_been_ingested_returns_false(self, s3_object_processor):
        assert not s3_object_processor.has_object_been_ingested(TEST_OBJECT_KEY)

    def test_get_last_ingestion_datetime_with_one_record(self, s3_object_processor):
        object_created_datetime = datetime(2024, 11, 24, 10, 00, 00, tzinfo=timezone.utc)
        IngestedObjectFactory(object_key=TEST_OBJECT_KEY, object_created=object_created_datetime)
        assert s3_object_processor.get_last_ingestion_datetime() == object_created_datetime

    def test_get_last_ingestion_datetime_with_multiple_records(self, s3_object_processor):
        older_target_object_key = f'{TEST_PREFIX}/a.jsonl.gz'
        most_recent_target_object_key = f'{TEST_PREFIX}/b.jsonl.gz'
        other_object_key = 'other/prefix/a.jsonl.gz'

        now = datetime.now(tz=timezone.utc)
        yesterday = now - timedelta(1)
        day_before_yesterday = now - timedelta(2)

        IngestedObjectFactory(
            object_key=older_target_object_key,
            object_created=day_before_yesterday,
        )
        most_recently_ingested_object_record = IngestedObjectFactory(
            object_key=most_recent_target_object_key,
            object_created=yesterday,
        )
        IngestedObjectFactory(
            object_key=other_object_key,
            object_created=now,
        )

        assert s3_object_processor.get_last_ingestion_datetime() == \
            most_recently_ingested_object_record.object_created

    def test_get_last_ingestion_datetime_with_no_records(self, s3_object_processor):
        assert s3_object_processor.get_last_ingestion_datetime() is None
