from django.conf import settings
from django.http import HttpResponse
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.views import APIView

from datahub.core.api_client import APIClient, TokenAuth
from datahub.core.view_utils import enforce_request_content_type
from datahub.dnb_api.constants import FEATURE_FLAG_DNB_COMPANY_SEARCH
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.oauth.scopes import Scope


class DNBCompanySearchView(APIView):
    """
    View for searching DNB companies.
    """

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (IsAuthenticatedOrTokenHasScope,)

    @enforce_request_content_type('application/json')
    def post(self, request):
        """Proxy for POST requests."""
        if not is_feature_flag_active(FEATURE_FLAG_DNB_COMPANY_SEARCH):
            return HttpResponse(
                status=status.HTTP_404_NOT_FOUND,
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
