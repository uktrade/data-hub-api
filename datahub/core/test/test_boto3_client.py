from unittest import mock


from django.test import override_settings

from datahub.core.boto3_client import get_s3_client


class TestBoto3Client:
    @override_settings(S3_LOCAL_ENDPOINT_URL='http://localstack')
    def test_get_s3_client_returns_local_instance(self):
        with mock.patch('datahub.core.boto3_client.boto3.client') as mock_s3_client:
            get_s3_client('region_1')
            mock_s3_client.assert_called_with('s3', 'region_1', endpoint_url='http://localstack')
