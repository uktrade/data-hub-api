import pytest

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.constants import (
    S3_BUCKET_NAME,
    TEST_PREFIX,
)


@pytest.fixture
def prefix():
    return TEST_PREFIX


@pytest.fixture
def bucket_name():
    return S3_BUCKET_NAME


@pytest.fixture
def s3_object_processor(s3_client, prefix):
    """Fixture for an S3ObjectProcessor instance."""
    return S3ObjectProcessor(
        prefix=prefix,
        bucket=S3_BUCKET_NAME,
        s3_client=s3_client,
    )
