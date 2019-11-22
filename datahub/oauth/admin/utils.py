import logging
from urllib.parse import urlencode

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from requests import HTTPError
from rest_framework.exceptions import AuthenticationFailed

from datahub.company.models import Advisor
from datahub.core.api_client import APIClient, TokenAuth

logger = logging.getLogger(__name__)


def get_access_token(code, redirect_uri):
    """Fetch OAuth2 access token from remote server."""
    oauth_params = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': settings.ADMIN_OAUTH2_CLIENT_ID,
        'client_secret': settings.ADMIN_OAUTH2_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
    }
    response = _get_api_client().request(
        'POST',
        settings.ADMIN_OAUTH2_TOKEN_FETCH_PATH,
        params=oauth_params,
    )

    access_token_data = response.json()
    if 'error' in access_token_data:
        raise AuthenticationFailed(access_token_data['error'])

    if 'access_token' not in access_token_data:
        raise AuthenticationFailed('No access token.')

    return access_token_data


def get_sso_user_profile(access_token):
    """Fetch a user profile using given access token from remote server."""
    try:
        api_client = _get_api_client(access_token)
        response = api_client.request('GET', settings.ADMIN_OAUTH2_USER_PROFILE_PATH)
    except HTTPError as exc:
        logger.warning(f'Cannot get user profile: {exc}')
        raise AuthenticationFailed('Cannot get user profile.') from exc

    return response.json()


def get_adviser_by_sso_user_profile(sso_user_profile):
    """Get adviser by sso user profile details."""
    try:
        user = Advisor.objects.get(email=sso_user_profile['email'], is_staff=True, is_active=True)
    except Advisor.DoesNotExist:
        raise AuthenticationFailed('User not found.')

    return user


def get_safe_next_url_from_request(request):
    """Get safe next URL from request."""
    next_url = request.GET.get('next')
    if url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return None


def build_redirect_uri(request, location):
    """Build redirect URI."""
    absolute_uri = request.build_absolute_uri(location)

    next_url = get_safe_next_url_from_request(request)
    if next_url:
        params = urlencode({'next': next_url})
        return f'{absolute_uri}?{params}'

    return absolute_uri


def _get_api_client(token=None):
    token = TokenAuth(token, 'Bearer') if token else None
    return APIClient(
        settings.ADMIN_OAUTH2_BASE_URL,
        auth=token,
        raise_for_status=True,
        default_timeout=settings.ADMIN_OAUTH2_REQUEST_TIMEOUT,
    )
