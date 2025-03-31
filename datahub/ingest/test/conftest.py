import pytest

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.constants import (
    TEST_AWS_REGION,
    TEST_PREFIX,
    TEST_S3_BUCKET_NAME,
)
from datahub.ingest.utils import compressed_json_faker


@pytest.fixture
def s3_object_processor(s3_client):
    """Fixture for an S3ObjectProcessor instance."""
    return S3ObjectProcessor(
        prefix=TEST_PREFIX,
        region=TEST_AWS_REGION,
        bucket=TEST_S3_BUCKET_NAME,  # Name of bucket created by the s3_client fixture
        s3_client=s3_client,
    )


@pytest.fixture
def test_object_tuples():
    """Fixture to create a list of object definitions.

    Each object is defined as a tuple in the form (key, content).
    """
    # Keys
    paths = [
        'file_a.jsonl.gz',
        'file_b.jsonl.gz',
        'file_c.jsonl.gz',
    ]
    keys = [f'{TEST_PREFIX}{path}' for path in paths]
    # Contents
    contents = [
        compressed_json_faker([{'test': 'content'}])
        for _ in range(len(keys))
    ]
    return [
        (key, content)
        for key, content
        in list(zip(keys, contents, strict=False))
    ]
