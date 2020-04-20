import logging
from secrets import token_urlsafe
from time import time
from urllib.parse import urlencode
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.admin import site
from django.contrib.auth import login as django_login, logout as django_logout
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed

from datahub.oauth.admin_sso.utils import (
    build_redirect_uri,
    get_access_token,
    get_adviser_by_sso_user_profile,
    get_safe_next_url_from_request,
    get_sso_user_profile,
)

logger = logging.getLogger(__name__)


ERROR_PAGE_TEMPLATE = 'admin/oauth/error.html'


def login(request):
    """
    View replacing Django admin login page.

    Instead of using standard Django authentication, we use OAuth2 protocol to authenticate user.
    """
    state_id = token_urlsafe(settings.ADMIN_OAUTH2_TOKEN_BYTE_LENGTH)
    redirect_uri = build_redirect_uri(request, reverse('admin_oauth_callback'))

    oauth_url_params = {
        'response_type': 'code',
        'client_id': settings.ADMIN_OAUTH2_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'state': state_id,
        'idp': 'cirrus',
    }
    authorization_url = urljoin(settings.ADMIN_OAUTH2_BASE_URL, settings.ADMIN_OAUTH2_AUTH_PATH)
    authorization_redirect_url = f'{authorization_url}?{urlencode(oauth_url_params)}'
    request.session['oauth.state'] = state_id
    return redirect(authorization_redirect_url)


def logout(request):
    """Perform Django log out and redirect to SSO log out."""
    django_logout(request)
    logout_url = urljoin(settings.ADMIN_OAUTH2_BASE_URL, settings.ADMIN_OAUTH2_LOGOUT_PATH)
    return redirect(logout_url)


def callback(request):
    """
    OAuth2 callback.

    1. Check if given state matches the state stored in session.
    2. Get access token using provided code.
    3. Request SSO profile using access token.
    4. Find an active user matching SSO profile and having `is_staff` flag.
    5. Store user details in session.
    """
    request_state_id = request.GET.get('state')
    if request_state_id is None:
        # if state is missing then restart login process, include next URL if possible
        redirect_uri = build_redirect_uri(request, reverse('admin:login'))
        return redirect(redirect_uri)

    state_id = request.session['oauth.state']
    if state_id != request_state_id:
        return error_response(request, 'State mismatch.')

    del request.session['oauth.state']

    code = request.GET.get('code')
    if code is None:
        return error_response(request, 'Forbidden.')

    try:
        redirect_uri = build_redirect_uri(request, reverse('admin_oauth_callback'))
        access_token_data = get_access_token(code, redirect_uri)
        sso_user_profile = get_sso_user_profile(access_token_data['access_token'])
        user = get_adviser_by_sso_user_profile(sso_user_profile)
    except AuthenticationFailed as exc:
        logger.warning(f'Django Admin OAuth2 authentication failed: {exc}')
        return error_response(request, 'Forbidden.')

    django_login(request, user)
    request.session['oauth.expires_on'] = int(time()) + access_token_data['expires_in']

    next_url = get_safe_next_url_from_request(request)
    if next_url:
        return redirect(next_url)

    return redirect(reverse('admin:index'))


def error_response(request, error):
    """View that displays an error."""
    context = {
        'title': 'Authentication problem',
        'error': error,
    }

    request.current_app = site.name

    return TemplateResponse(
        request,
        ERROR_PAGE_TEMPLATE,
        context,
        status=status.HTTP_403_FORBIDDEN,
    )
