from contextlib import contextmanager
from hashlib import sha256
from itertools import zip_longest
from logging import getLogger
from urllib.parse import urlparse

import boto3
import requests
from django.conf import settings

logger = getLogger(__name__)


def generate_enum_code_from_queryset(model_queryset):
    """Generate the Enum code for a given constant model queryset.

    Paste the generated text into the constants file.
    """
    for q in model_queryset:
        var_name = q.name.replace(' ', '_').lower()
        return f"{var_name} = Constant('{q.name}', '{q.id}')"


@contextmanager
def log_and_ignore_exceptions():
    """Write non-fatal exceptions to the log and ignore them afterwards."""
    try:
        yield
    except Exception:
        logger.exception('Silently ignoring non-fatal exception')


def stream_to_file_pointer(url, fp):
    """Efficiently stream given url to given file pointer."""
    response = requests.get(url, stream=True)
    for chunk in response.iter_content(chunk_size=4096):
        fp.write(chunk)


def string_to_bytes(obj):
    """Cast string to bytes."""
    if type(obj) is str:
        return bytes(obj, 'utf-8')
    return obj


def generate_signature(path, body, salt):
    """Generate the signature to be passed into the header."""
    # make sure it's a path
    url_object = urlparse(path)
    message = string_to_bytes(url_object.path) + string_to_bytes(body) + string_to_bytes(salt)
    return sha256(message).hexdigest()


def slice_iterable_into_chunks(iterable, size):
    """Collect data into fixed-length chunks or blocks.

    https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    args = [iter(iterable)] * size
    return zip_longest(*args, fillvalue=None)


def sign_s3_url(bucket_name, path, expires=3600):
    """Sign s3 url using global config, and given expiry in seconds."""
    s3 = boto3.client(
        's3',
        region_name='eu-west-2',
        aws_access_key_id=settings.AWS_ACCESS['KEY_ID'],
        aws_secret_access_key=settings.AWS_ACCESS['KEY_SECRET'],
    )

    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket_name,
            'Key': path,
        },
        ExpiresIn=expires,
    )
