import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from datahub.ingest.constants import (
    AWS_REGION,
    S3_BUCKET_NAME,
)
from datahub.ingest.models import IngestedObject

logger = logging.getLogger(__name__)


def get_s3_client(region: str):
    if settings.S3_LOCAL_ENDPOINT_URL:
        logger.debug('Using local S3 endpoint %s', settings.S3_LOCAL_ENDPOINT_URL)
        return boto3.client('s3', region, endpoint_url=settings.S3_LOCAL_ENDPOINT_URL)
    return boto3.client('s3', region)


class S3ObjectProcessor:
    """Base class for processing objects located at a specified prefix within an S3 bucket."""

    def __init__(
        self,
        prefix: str,
        region: str = AWS_REGION,
        bucket: str = S3_BUCKET_NAME,
        s3_client=None,
    ) -> None:
        self.prefix = prefix
        self.region = region
        self.bucket = bucket
        if s3_client is None:
            self.s3_client = get_s3_client(region)
        else:
            self.s3_client = s3_client

    def list_objects(self) -> list[str]:
        """Returns a list of metadata about each object located at self.prefix.

        From the boto3 docs, the metadata will contain the following:
        - Key (string) - the name that you assign the object
        - LastModified (datetime) - creation date of the object
        - ETag (string) - entity tag; a hash of the object
        - ChecksumAlgorithm (list) - the algorithm used to create a checksum of the object
        - Size (integer) - size in bytes of the object
        - StorageClass (string) - the class of storage used to store the object
        - Owner (dict) - the owner of the object
        - RestoreStatus (dict) - the restoration status of the the object
        """
        response = self.s3_client.list_objects(
            Bucket=self.bucket,
            Prefix=self.prefix,
        )
        return response.get('Contents', [])

    def get_most_recent_object_key(self) -> str:
        """Return the most recent object's key in the self.bucket at self.prefix."""
        objects = self.list_objects()
        if not objects:
            return None
        most_recent_object = max(objects, key=lambda x: x['LastModified'])
        return most_recent_object['Key']

    def get_object_last_modified_datetime(self, object_key: str) -> datetime:
        """Get last modified datetime of a specific object."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            return response.get('LastModified')
        except ClientError as e:
            logger.error(
                f'Error getting last modified datetime for {object_key}: {str(e)}',
            )
            raise e

    def has_object_been_ingested(self, object_key: str) -> bool:
        """Determines if the specified object has already been ingested."""
        return IngestedObject.objects.filter(object_key=object_key).exists()

    def get_last_ingestion_datetime(self) -> datetime | None:
        """Get last ingestion datetime of an object with the same prefix (directory)."""
        try:
            return IngestedObject.objects.filter(
                object_key__icontains=self.prefix,
            ).latest('object_created').object_created
        except IngestedObject.DoesNotExist:
            return None
