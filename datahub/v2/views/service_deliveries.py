import functools

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import encoding
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import parsers
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from datahub.core.permissions import method_permission_required
from datahub.oauth.scopes import Scope
from datahub.v2.parsers import JSONParser
from datahub.v2.renderers import JSONRenderer
from datahub.v2.repos import service_deliveries as service_deliveries_repos


class ServiceDeliveryListViewV2(APIView):
    """Service delivery list view."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.internal_front_end,)
    repo_class = service_deliveries_repos.ServiceDeliveryDatabaseRepo
    param_keys = frozenset({'company_id', 'contact_id', 'offset', 'limit'})
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    parser_classes = (JSONParser, parsers.FormParser, parsers.MultiPartParser)
    detail_view_name = 'api-v2:servicedelivery-detail'
    entity_name = 'ServiceDelivery'

    @method_permission_required('interaction.read_servicedelivery')
    def get(self, request):
        """Handle the GET."""
        params = {k: v for (k, v) in request.query_params.items() if k in self.param_keys}
        url_builder = functools.partial(
            reverse, viewname=self.detail_view_name, request=request)
        repo_config = {'url_builder': url_builder}
        service_deliveries = self.repo_class(config=repo_config).filter(**params)
        return Response(service_deliveries)

    @method_permission_required('interaction.add_servicedelivery')
    def post(self, request):
        """Handle the POST.

        Objects are created and update through a POST request.
        """
        data = self.inject_adviser(request)
        url_builder = functools.partial(
            reverse, viewname=self.detail_view_name, request=request)
        repo_config = {'url_builder': url_builder}
        service_delivery = self.repo_class(config=repo_config).upsert(data)
        return Response(service_delivery)

    @staticmethod
    def inject_adviser(request):
        """Add the adviser id to the data."""
        data = dict(request.data)
        data['relationships'].update({
            'dit_adviser': {
                'data': {
                    'type': 'Adviser',
                    'id': encoding.force_text(request.user.pk)}
            }
        })
        return data


class ServiceDeliveryDetailViewV2(APIView, PermissionRequiredMixin):
    """Service delivery detail view."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.internal_front_end,)
    repo_class = service_deliveries_repos.ServiceDeliveryDatabaseRepo
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    parser_classes = (JSONParser, parsers.FormParser, parsers.MultiPartParser)
    detail_view_name = 'api-v2:servicedelivery-detail'
    entity_name = 'ServiceDelivery'

    @method_permission_required(perm='interaction.read_servicedelivery')
    def get(self, request, object_id):
        """Handle the GET."""
        url_builder = functools.partial(
            reverse, viewname=self.detail_view_name, request=request)
        repo_config = {'url_builder': url_builder}
        service_delivery = self.repo_class(config=repo_config).get(object_id=object_id)
        return Response(service_delivery)
