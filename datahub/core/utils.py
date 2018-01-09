from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from itertools import islice
from logging import getLogger

import boto3
import requests

executor = ThreadPoolExecutor()
logger = getLogger(__name__)


class StrEnum(str, Enum):
    """
    Enum subclass where members are also str instances.

    Defined as per https://docs.python.org/3.6/library/enum.html#others
    """


def generate_enum_code_from_queryset(model_queryset):
    """Generate the Enum code for a given constant model queryset.

    Paste the generated text into the constants file.
    """
    for q in model_queryset:
        var_name = q.name.replace(' ', '_').lower()
        return f"{var_name} = Constant('{q.name}', '{q.id}')"


def stream_to_file_pointer(url, fp):
    """Efficiently stream given url to given file pointer."""
    response = requests.get(url, stream=True)
    for chunk in response.iter_content(chunk_size=4096):
        fp.write(chunk)


def slice_iterable_into_chunks(iterable, batch_size, obj_creator):
    """Collect data into fixed-length chunks or blocks."""
    iterator = iter(iterable)
    while True:
        batch_iter = islice(iterator, batch_size)
        objects = [obj_creator(row) for row in batch_iter]
        if not objects:
            break
        yield objects


def shut_down_thread_pool():
    """Shuts down the thread pool."""
    logger.info('Shutting down thread pool...')
    executor.shutdown()


def get_s3_client():
    """Get S3 client singleton."""
    s3 = getattr(get_s3_client, 's3_instance', None)
    if not s3:
        get_s3_client.s3_instance = s3 = boto3.client('s3')

    return s3


def sign_s3_url(bucket_name, path, method='get_object', expires=3600, client=None):
    """Sign s3 url using global config, and given expiry in seconds."""
    if client is None:
        client = get_s3_client()

    return client.generate_presigned_url(
        ClientMethod=method,
        Params={
            'Bucket': bucket_name,
            'Key': path,
        },
        ExpiresIn=expires,
    )


def delete_s3_obj(bucket, key, client=None):
    """Remove object from S3 Bucket."""
    if client is None:
        client = get_s3_client()

    response = client.delete_object(
        Bucket=bucket,
        Key=key,
    )

    assert response['ResponseMetadata']['HTTPStatusCode'] == 204


def load_constants_to_database(constants, model):
    """Loads an iterable of constants (typically an Enum) for a model to the database."""
    for constant in constants:
        model_obj, created = model.objects.get_or_create(pk=constant.value.id)
        if created or model_obj.name != constant.value.name:
            if created:
                logger.info('Creating %s "%s"', model._meta.verbose_name, constant.value.name)
            else:
                logger.info('Updating name of %s "%s" to "%s"',
                            model._meta.verbose_name,
                            model_obj.name,
                            constant.value.name)

            model_obj.name = constant.value.name
            model_obj.save()
