from functools import lru_cache
from logging import getLogger

import boto3
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from datahub.core.exceptions import DataHubError
from datahub.documents.exceptions import DocumentDeleteException
from datahub.ingest.boto3 import get_s3_client
from datahub.ingest.constants import AWS_REGION

logger = getLogger(__name__)


def get_document_by_pk(document_pk):
    """Get Document by pk.

    This is to avoid circular imports from av_scan and tasks.
    """
    try:
        document_model = apps.get_model('documents', 'Document')
        document = document_model.objects.get(pk=document_pk)
        return document
    except ObjectDoesNotExist:
        logger.warning(f'Document with ID {document_pk} does not exist.')
        return None


def get_bucket_credentials(bucket_id):
    """Get S3 credentials for bucket id."""
    if bucket_id not in settings.DOCUMENT_BUCKETS:
        raise DataHubError(f'Bucket "{bucket_id}" not configured.')

    return settings.DOCUMENT_BUCKETS[bucket_id]


def get_bucket_name(bucket_id):
    """Get bucket name for given bucket id."""
    return get_bucket_credentials(bucket_id)['bucket']


@lru_cache()
def get_s3_client_for_bucket(bucket_id, use_default_credentials=False):
    """Get S3 client for bucket id.

    Args:
        bucket_id: The bucket ID to get the client for
        use_default_credentials: If True, uses default AWS credentials instead of specific ones

    """
    if use_default_credentials:
        # TODO: check if need to pass config arg to default client
        return get_s3_client(AWS_REGION)

    credentials = get_bucket_credentials(bucket_id)
    return boto3.client(
        's3',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        region_name=credentials['aws_region'],
        config=boto3.session.Config(signature_version='s3v4'),
    )


def sign_s3_url(bucket_id, key, method='get_object', expires=3600, use_default_credentials=False):
    """Sign s3 url with given expiry in seconds."""
    client = get_s3_client_for_bucket(bucket_id, use_default_credentials=use_default_credentials)

    if use_default_credentials:
        bucket_name = bucket_id
    else:
        bucket_name = get_bucket_name(bucket_id)

    return client.generate_presigned_url(
        ClientMethod=method,
        Params={
            'Bucket': bucket_name,
            'Key': key,
        },
        ExpiresIn=expires,
    )


def perform_delete_document(document_pk):
    """Deletes Document and corresponding S3 file.

    :raises: DocumentDeleteException if document:
        - doesn't have status=UploadStatus.DELETION_PENDING
        - response from S3 doesn't declare no content (status_code=204)
        - doesn't exist
    :raises: botocore.exceptions.ClientError if there was a problem with the S3 client


    :param document_pk: id of the Document
    """
    from datahub.documents.models import UploadStatus

    document = get_document_by_pk(document_pk)
    if not document:
        raise DocumentDeleteException(
            f'Document with ID {document_pk} not found.',
        )

    if document.status != UploadStatus.DELETION_PENDING:
        raise DocumentDeleteException(
            f'Document with ID {document_pk} is not pending deletion.',
        )

    if document.path:
        bucket_id = document.bucket_id

        client = get_s3_client_for_bucket(
            bucket_id,
            use_default_credentials=document.use_default_credentials,
        )

        if document.use_default_credentials:
            bucket_name = bucket_id
        else:
            bucket_name = get_bucket_name(bucket_id)

        client.delete_object(Bucket=bucket_name, Key=document.path)

    document.delete()


def delete_document(bucket_id, document_key):
    """Deletes document in S3 bucket."""
    client = get_s3_client_for_bucket(bucket_id=bucket_id)
    client.delete_object(Bucket=get_bucket_name(bucket_id=bucket_id), Key=document_key)


def format_content_type(content_type_instance: ContentType):
    """Return a string representation of the content type in the form: `app_label.model`."""
    return f'{content_type_instance.app_label}.{content_type_instance.model}'
