import gzip
from datetime import datetime, timedelta

import pytest
from django.core.cache import cache
from freezegun import freeze_time

from datahub.interaction.admin_csv_import.cache_utils import (
    _cache_key_for_token,
    CACHE_VALUE_TIMEOUT,
    CacheKeyType,
    load_file_contents_and_name,
    load_unmatched_rows_csv_contents,
    save_file_contents_and_name,
    save_unmatched_rows_csv_contents,
)


@pytest.mark.usefixtures('local_memory_cache')
class TestLoadFileContentsAndName:
    """Tests for load_file_contents_and_name()."""

    def test_loads_contents_and_name(self):
        """Test load_file_contents_and_name()."""
        token = 'test-token'
        contents_key = _cache_key_for_token(token, CacheKeyType.file_contents)
        name_key = _cache_key_for_token(token, CacheKeyType.file_name)

        contents = b'file-contents'
        name = 'file-name'

        cache.set(contents_key, gzip.compress(contents))
        cache.set(name_key, name)

        loaded_contents, loaded_name = load_file_contents_and_name(token)

        assert loaded_contents == contents
        assert loaded_name == name

    @pytest.mark.parametrize(
        'cache_data',
        (
            # only the file contents
            {_cache_key_for_token('test-token', CacheKeyType.file_contents): b'data'},
            # only the file name
            {_cache_key_for_token('test-token', CacheKeyType.file_name): 'name'},
            # nothing
            {},
        ),
    )
    def test_returns_none_if_any_key_not_found(self, cache_data):
        """Test that load_file_contents_and_name() returns None if a cache key is missing."""
        cache.set_many(cache_data)

        assert load_file_contents_and_name('test-token') is None


@pytest.mark.usefixtures('local_memory_cache')
class TestSaveFileContentsAndName:
    """Tests for save_file_contents_and_name()."""

    def test_saves_file_contents_and_name(self):
        """Test that the file is saved in the cache."""
        contents = b'file-contents'
        name = 'file-name'
        token = 'test-token'

        save_file_contents_and_name(token, contents, name)

        contents_key = _cache_key_for_token(token, CacheKeyType.file_contents)
        name_key = _cache_key_for_token(token, CacheKeyType.file_name)

        assert cache.get(name_key) == name

        saved_contents = gzip.decompress(cache.get(contents_key))
        assert saved_contents == contents


@pytest.mark.usefixtures('local_memory_cache')
class TestLoadUnmatchedRowsCSVContents:
    """Tests for load_unmatched_rows_csv_contents()."""

    def test_loads_unmatched_rows(self):
        """Test that the file is loaded from the cache."""
        contents = b'file-contents'
        token = 'test-token'

        key = _cache_key_for_token(token, CacheKeyType.unmatched_rows)
        cache.set(key, gzip.compress(contents))

        assert load_unmatched_rows_csv_contents(token) == contents


@pytest.mark.usefixtures('local_memory_cache')
class TestSaveUnmatchedRowsCSVContents:
    """Tests for save_unmatched_rows_csv_contents()."""

    def test_saves_unmatched_rows(self):
        """Test that the file is saved to the cache."""
        contents = b'file-contents'
        token = 'test-token'

        save_unmatched_rows_csv_contents(token, contents)

        key = _cache_key_for_token(token, CacheKeyType.unmatched_rows)
        saved_contents = gzip.decompress(cache.get(key))
        assert saved_contents == contents

    def test_key_expires(self):
        """Test that the key expires after the expiry period."""
        contents = b'file-contents'
        token = 'test-token'
        base_datetime = datetime(2019, 2, 3)

        with freeze_time(base_datetime):
            save_unmatched_rows_csv_contents(token, contents)

        key = _cache_key_for_token(token, CacheKeyType.unmatched_rows)

        with freeze_time(base_datetime + CACHE_VALUE_TIMEOUT + timedelta(minutes=1)):
            assert cache.get(key) is None


class TestCacheKeyForToken:
    """Tests for _cache_key_for_token()."""

    @pytest.mark.parametrize(
        'token,type_,key',
        (
            ('token1', CacheKeyType.file_contents, 'interaction-csv-import:token1:file-contents'),
            ('token2', CacheKeyType.file_name, 'interaction-csv-import:token2:file-name'),
        ),
    )
    def test_generates_keys(self, token, type_, key):
        """Test that the expected keys are generated."""
        assert _cache_key_for_token(token, type_) == key

    @pytest.mark.parametrize(
        'token,type_,error',
        (
            (None, CacheKeyType.file_contents, ValueError),
            ('', CacheKeyType.file_contents, ValueError),
            ('token', None, TypeError),
        ),
    )
    def test_raises_error_on_invalid_input(self, token, type_, error):
        """Test that an error is raised if an invalid token or type_ is provided."""
        with pytest.raises(error):
            _cache_key_for_token(token, type_)
