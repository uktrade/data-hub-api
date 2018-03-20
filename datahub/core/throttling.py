import hashlib

from rest_framework.throttling import SimpleRateThrottle


class PathRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls based on the path used
    instead of the user logged-in or the client IP.

    This is useful with views without user authentication where
    the path includes user-related resources.

    E.g. /user/<user-token>/forgot-password/

    Note: query params are ignored.
    """

    def get_cache_key(self, request, view):
        """
        :returns: cache key constructed from the request path
        """
        # we hash the path to have a deterministic length (64 chars)
        ident_hash = hashlib.sha256(request.path.lower().encode('utf-8'))

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident_hash.hexdigest()
        }
