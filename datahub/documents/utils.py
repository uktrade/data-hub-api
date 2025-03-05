from datetime import datetime
from functools import lru_cache
from logging import getLogger

import boto3

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from datahub.core.exceptions import DataHubError
from datahub.documents.exceptions import DocumentDeleteException


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


logger = getLogger(__name__)


def get_document_by_pk(document_pk):
    """
    Get Document by pk.

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
def get_s3_client_for_bucket(bucket_id):
    """Get S3 client for bucket id."""
    credentials = get_bucket_credentials(bucket_id)
    return boto3.client(
        's3',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        region_name=credentials['aws_region'],
        config=boto3.session.Config(signature_version='s3v4'),
    )


def sign_s3_url(bucket_id, key, method='get_object', expires=3600):
    """Sign s3 url with given expiry in seconds."""
    client = get_s3_client_for_bucket(bucket_id)
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
    """
    Deletes Document and corresponding S3 file.

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

        client = get_s3_client_for_bucket(bucket_id)
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


def assert_retrieved_sharepoint_document(instance, retrieved_instance):
    """Asserts retrieved JSON contains the correct fields and data from the SharePointDocument."""
    assert str(instance.id) == retrieved_instance['id']

    assert str(instance.created_by.id) == retrieved_instance['created_by']['id']
    assert str(instance.modified_by.id) == retrieved_instance['modified_by']['id']

    assert instance.created_on.timestamp() == \
        datetime.strptime(retrieved_instance['created_on'], DATETIME_FORMAT).timestamp()
    assert instance.modified_on.timestamp() == \
        datetime.strptime(retrieved_instance['modified_on'], DATETIME_FORMAT).timestamp()

    assert instance.archived == retrieved_instance['archived']
    assert instance.archived_on == retrieved_instance['archived_on']
    assert instance.archived_reason == retrieved_instance['archived_reason']

    assert instance.title == retrieved_instance['title']
    assert instance.url == retrieved_instance['url']


def assert_retrieved_generic_document(instance, retrieved_instance):
    """Asserts retrieved JSON contains the correct fields and data from the GenericDocument."""
    assert str(instance.id) == retrieved_instance['id']

    assert str(instance.created_by.id) == retrieved_instance['created_by']['id']
    assert str(instance.modified_by.id) == retrieved_instance['modified_by']['id']

    assert instance.created_on.timestamp() == \
        datetime.strptime(retrieved_instance['created_on'], DATETIME_FORMAT).timestamp()
    assert instance.modified_on.timestamp() == \
        datetime.strptime(retrieved_instance['modified_on'], DATETIME_FORMAT).timestamp()

    assert instance.archived == retrieved_instance['archived']
    assert instance.archived_on == retrieved_instance['archived_on']
    assert instance.archived_reason == retrieved_instance['archived_reason']

    assert str(instance.document.id) == retrieved_instance['document']['id']
    assert str(instance.related_object.id) == retrieved_instance['related_object']['id']
    assert str(instance.document_object_id) == retrieved_instance['document_object_id']
    assert str(instance.related_object_id) == retrieved_instance['related_object_id']

    assert format_content_type(instance.document_type) == retrieved_instance['document_type']
    assert format_content_type(instance.related_object_type) == \
        retrieved_instance['related_object_type']
