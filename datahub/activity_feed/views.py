from django.conf import settings
from django.http import HttpResponse
from django.http.multipartparser import parse_header
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import HTTP_HEADER_ENCODING, status
from rest_framework.views import APIView

from datahub.core.api_client import APIClient, HawkAuth
from datahub.oauth.scopes import Scope


class ActivityFeedView(APIView):
    """
    Activity Feed View.

    At the moment it just authenticates the user using the default authentication
    for the internal_front_end and acts as a proxy for reading from Activity Stream.
    """

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (IsAuthenticatedOrTokenHasScope,)

    def get(self, request):
        """Proxy for GET requests."""
        content_type = request.content_type or ''
        base_media_type, _ = parse_header(content_type.encode(HTTP_HEADER_ENCODING))
        if base_media_type != 'application/json':
            return HttpResponse(
                'Please set Content-Type header value to application/json',
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        hawk_auth = HawkAuth(
            settings.ACTIVITY_STREAM_OUTGOING_ACCESS_KEY_ID,
            settings.ACTIVITY_STREAM_OUTGOING_SECRET_ACCESS_KEY,
            verify_response=False,
        )

        api_client = APIClient(
            settings.ACTIVITY_STREAM_OUTGOING_URL,
            hawk_auth,
            raise_for_status=False,
        )
        response = api_client.request(
            request.method,
            '',
            data=request.body,
            headers={
                'Content-Type': request.content_type,
            },
        )
        return HttpResponse(
            response.text,
            status=response.status_code,
            content_type=response.headers.get('content-type'),
        )
