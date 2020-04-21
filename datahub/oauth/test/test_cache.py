from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.oauth.cache import add_token_data_to_cache, get_token_data_from_cache


@pytest.mark.usefixtures('local_memory_cache')
class TestAddTokenDataToCache:
    """Tests for test_add_token_data_to_cache()."""

    def test_returns_cached_data(self):
        """The data as stored in the cached should be returned."""
        token = 'test-token'
        email = 'email@datahub.test'
        sso_email_user_id = 'id@datahub.test'

        frozen_time = now()
        with freeze_time(frozen_time):
            returned_data = add_token_data_to_cache(token, email, sso_email_user_id, 10)

        assert returned_data == {
            'email': email,
            'sso_email_user_id': sso_email_user_id,
        }

    def test_adds_data_to_cache(self):
        """The data should be added to the cache."""
        token = 'test-token'
        email = 'email@datahub.test'
        sso_email_user_id = 'id@datahub.test'

        expected_data = {
            'email': email,
            'sso_email_user_id': sso_email_user_id,
        }

        frozen_time = now()
        with freeze_time(frozen_time):
            add_token_data_to_cache(token, email, sso_email_user_id, 10)

        cache_key = 'access_token:test-token'
        assert cache.get(cache_key) == expected_data

        # The data should expire after 10 seconds
        with freeze_time(frozen_time + timedelta(seconds=10)):
            assert cache.get(cache_key) is None


@pytest.mark.usefixtures('local_memory_cache')
class TestGetTokenDataFromCache:
    """Tests for get_token_data_from_cache()."""

    def test_retrieves_cached_data(self):
        """Cached data should be returned when present."""
        cache_key = 'access_token:test-token'
        token = 'test-token'

        data = {
            'email': 'email@datahub.test',
            'sso_email_user_id': 'id@datahub.test',
        }
        cache.set(cache_key, data)

        assert get_token_data_from_cache(token) == data

    def test_returns_none_when_not_cached(self):
        """None should be returned when there is no cached data for the token."""
        token = 'test-token'
        assert get_token_data_from_cache(token) is None
