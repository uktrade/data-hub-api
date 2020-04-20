from urllib.parse import parse_qs, urlparse

from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory


def get_request_with_session(path):
    """Get request with attached session."""
    request_factory = RequestFactory()
    request = request_factory.get(path)
    session_middleware = SessionMiddleware()
    session_middleware.process_request(request)
    authentication_middleware = AuthenticationMiddleware()
    authentication_middleware.process_request(request)
    return request


def extract_next_url_from_url(url):
    """Extract next URL from URL."""
    parsed_url = urlparse(url)
    parsed_qs = parse_qs(parsed_url.query)
    if 'next' in parsed_qs:
        return parsed_qs['next'][0]

    return None


def extract_next_url_from_redirect_url(redirect_uri):
    """Extract next URL from redirect URI."""
    parsed_url = urlparse(redirect_uri)
    parsed_qs = parse_qs(parsed_url.query)

    redirect_uri = parsed_qs['redirect_uri'][0]
    return extract_next_url_from_url(redirect_uri)
