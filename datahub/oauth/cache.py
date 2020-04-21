from django.core.cache import cache


def add_token_data_to_cache(token, email, sso_email_user_id, timeout):
    """Add data about an access token to the cache."""
    cache_key = _cache_key(token)
    data = {
        'email': email,
        'sso_email_user_id': sso_email_user_id,
    }

    cache.set(cache_key, data, timeout=timeout)
    return data


def get_token_data_from_cache(token):
    """Retrieve data about an access token from the cache."""
    cache_key = _cache_key(token)
    return cache.get(cache_key)


def _cache_key(token):
    return f'access_token:{token}'
