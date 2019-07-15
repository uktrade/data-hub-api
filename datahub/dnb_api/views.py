from django.conf import settings
from django.http import HttpResponse
from django.http.multipartparser import parse_header
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import HTTP_HEADER_ENCODING, status
from rest_framework.views import APIView

from datahub.core.api_client import APIClient, TokenAuth
from datahub.oauth.scopes import Scope


class DNBCompanySearchView(APIView):
    """
    View for searching DNB companies.
    """

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (IsAuthenticatedOrTokenHasScope,)

    def post(self, request):
        """Proxy for POST requests."""
        # TODO: Break the following out in to an @enforce_media_type('application/json') dcorator
        # - this is shared with activity feed
        content_type = request.content_type or ''

        # check that the content type of the request is json
        base_media_type, _ = parse_header(content_type.encode(HTTP_HEADER_ENCODING))
        if base_media_type != 'application/json':
            return HttpResponse(
                'Please set Content-Type header value to application/json',
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        upstream_response = self._get_upstream_response(request)
        return HttpResponse(
            upstream_response.text,
            status=upstream_response.status_code,
            content_type=upstream_response.headers.get('content-type'),
        )

    def _get_upstream_response(self, request):

        search_endpoint = settings.DNB_SERVICE_BASE_URL + 'companies/search/'
        shared_key_auth = TokenAuth(settings.DNB_SERVICE_TOKEN)
        api_client = APIClient(
            search_endpoint,
            shared_key_auth,
            raise_for_status=False,
        )
        return api_client.request(
            request.method,
            '',
            data=request.body,
            headers={
                'Content-Type': request.content_type,
            },
        )
