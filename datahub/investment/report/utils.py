import boto3
from django.conf import settings


def get_report_s3_client():
    """Get S3 client singleton."""
    s3 = getattr(get_report_s3_client, 's3_instance', None)
    if not s3:
        get_report_s3_client.s3_instance = s3 = boto3.client(
            's3',
            aws_access_key_id=settings.REPORT_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.REPORT_AWS_SECRET_ACCESS_KEY,
            region_name=settings.REPORT_AWS_REGION,
            config=boto3.session.Config(signature_version='s3v4'),
        )

    return s3
