import logging

import boto3
from django.conf import settings

logger = logging.getLogger(__name__)


def get_s3_client(region):
    if settings.S3_LOCAL_ENDPOINT_URL:
        logger.debug('using local S3 endpoint %s', settings.S3_LOCAL_ENDPOINT_URL)
        return boto3.client('s3', region, endpoint_url=settings.S3_LOCAL_ENDPOINT_URL)

    return boto3.client('s3', region)
