from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from datahub.core.api_client import APIClient, HawkAuth
from datahub.core.view_utils import enforce_request_content_type


class ActivityFeedView(APIView):
    """
    Activity Feed View.

    At the moment it just authenticates the user using the default authentication
    for the internal_front_end and acts as a proxy for reading from Activity Stream.

    If the authenticated user doesn't have permissions on all activity models,
    it returns an empty list.
    """

    permission_classes = (IsAuthenticated,)

    ACTIVITY_MODELS_PERMISSIONS_REQUIRED = (
        'company_referral.view_companyreferral',
        'interaction.view_all_interaction',
        'investment.view_all_investmentproject',
        'investor_profile.view_largecapitalinvestorprofile',
        'order.view_order',
    )

    @method_decorator(enforce_request_content_type('application/json'))
    def get(self, request):
        """Proxy for GET requests."""
        content_type = request.content_type or ''
        # if the user doesn't have permissions on all activity models, return an empty list
        # TODO: instead of returning an empty list, we need to filter out the
        # activities that the user doesn't have access to
        if not request.user.has_perms(self.ACTIVITY_MODELS_PERMISSIONS_REQUIRED):
            return JsonResponse(
                {
                    'hits': {
                        'total': 0,
                        'hits': [],
                    },
                },
                status=status.HTTP_200_OK,
                content_type=content_type,
            )

        upstream_response = self._get_upstream_response(request)
        return HttpResponse(
            upstream_response.text,
            status=upstream_response.status_code,
            content_type=upstream_response.headers.get('content-type'),
        )

    def _get_upstream_response(self, request=None):
        hawk_auth = HawkAuth(
            settings.ACTIVITY_STREAM_OUTGOING_ACCESS_KEY_ID,
            settings.ACTIVITY_STREAM_OUTGOING_SECRET_ACCESS_KEY,
            verify_response=False,
        )

        api_client = APIClient(
            api_url=settings.ACTIVITY_STREAM_OUTGOING_URL,
            auth=hawk_auth,
            request=request,
            raise_for_status=False,
            default_timeout=settings.DEFAULT_SERVICE_TIMEOUT,
        )
        return api_client.request(
            request.method,
            '',
            data=request.body,
            headers={
                'Content-Type': request.content_type,
            },
        )
