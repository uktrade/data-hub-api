import boto3

from moto import mock_aws

from datahub.investment_lead.tasks.ingest_eyb_common import REGION
from datahub.investment_lead.test.factories import create_fake_file


@mock_aws
def setup_s3_client():
    return boto3.client('s3', REGION)


@mock_aws
def setup_s3_bucket(bucket_name, test_file_paths, test_file_contents=None):
    """Sets up a mocked S3 bucket.

    Note, if test_file_contents=None, it populates the specified file paths
    with fake triage records.
    """
    mock_s3_client = boto3.client('s3', REGION)
    mock_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': REGION},
    )
    if test_file_contents is None:
        test_file_contents = [
            create_fake_file(default_faker='triage')
            for _ in range(len(test_file_paths))
        ]
    for file_path, file_contents in zip(test_file_paths, test_file_contents):
        mock_s3_client.put_object(Bucket=bucket_name, Key=file_path, Body=file_contents)
