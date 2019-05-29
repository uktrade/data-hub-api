import gzip
from datetime import timedelta

from django.core.cache import cache

from datahub.core.utils import StrEnum

CACHE_VALUE_TIMEOUT_SECS = int(timedelta(minutes=30).total_seconds())


class CacheKeyType(StrEnum):
    """Types of cache keys used to store information about an import interactions operation."""

    file_name = 'file-name'
    file_contents = 'file-contents'
    result_counts_by_status = 'result_counts_by_status'


def load_file_contents_and_name(token):
    """Load a previously-saved file-contents-and-name pair from the cache."""
    contents_key = _cache_key_for_token(token, CacheKeyType.file_contents)
    name_key = _cache_key_for_token(token, CacheKeyType.file_name)
    cache_keys_and_values = cache.get_many((contents_key, name_key))

    any_cache_keys_missing = {contents_key, name_key} - cache_keys_and_values.keys()
    if any_cache_keys_missing:
        return None

    decompressed_contents = gzip.decompress(cache_keys_and_values[contents_key])
    name = cache_keys_and_values[name_key]
    return decompressed_contents, name


def save_file_contents_and_name(token, contents, name):
    """
    Save the contents of a file and the file's name to the cache.

    (This is used to store the file while the preview page is being displayed to the user.)
    """
    compressed_contents = gzip.compress(contents)

    contents_key = _cache_key_for_token(token, CacheKeyType.file_contents)
    name_key = _cache_key_for_token(token, CacheKeyType.file_name)

    cache_keys_and_values = {
        contents_key: compressed_contents,
        name_key: name,
    }
    cache.set_many(cache_keys_and_values, timeout=CACHE_VALUE_TIMEOUT_SECS)


def load_result_counts_by_status(token):
    """Load counts by matching status from the cache for a completed import operation."""
    result_counts_cache_key = _cache_key_for_token(token, CacheKeyType.result_counts_by_status)
    return cache.get(result_counts_cache_key)


def save_result_counts_by_status(token, counts_by_status):
    """Saves counts by matching status to the cache for a completed import operation."""
    result_counts_cache_key = _cache_key_for_token(token, CacheKeyType.result_counts_by_status)
    cache.set(result_counts_cache_key, counts_by_status, CACHE_VALUE_TIMEOUT_SECS)


def _cache_key_for_token(token, type_: CacheKeyType):
    # Technically we should raise TypeError if token is None, but the distinction isn't
    # particularly important here
    if not token:
        raise ValueError('A token is required.')

    if not isinstance(type_, CacheKeyType):
        raise TypeError('type_ must be an instance of CacheKeyType.')

    prefix = f'interaction-csv-import:{token}'
    return f'{prefix}:{type_}'
