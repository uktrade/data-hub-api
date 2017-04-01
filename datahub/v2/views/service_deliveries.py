import functools

from rest_framework import parsers
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from datahub.v2.parsers import JSONParser
from datahub.v2.renderers import JSONRenderer
from datahub.v2.repos import service_deliveries as service_deliveries_repos


class ServiceDeliveryListViewV2(APIView):
    """Service delivery list view."""

    repo_class = service_deliveries_repos.ServiceDeliveryDatabaseRepo
    param_keys = frozenset({'company_id', 'contact_id', 'offset', 'limit'})
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    parser_classes = (JSONParser, parsers.FormParser, parsers.MultiPartParser)
    detail_view_name = 'v2:servicedelivery-detail'
    entity_name = 'ServiceDelivery'

    def get(self, request):
        """Handle the GET."""
        params = {k: v for (k, v) in request.query_params.items() if k in self.param_keys}
        url_builder = functools.partial(
            reverse, viewname=self.detail_view_name, request=request)
        repo_config = {'url_builder': url_builder}
        service_deliveries = self.repo_class(config=repo_config).filter(**params)
        return Response(service_deliveries)

    def post(self, request):
        """Handle the POST."""
        data = dict(request.data)
        data.update({
            'dit_advisor': {
                'type': 'Advisor',
                'id': str(request.user.pk)}})
        url_builder = functools.partial(
            reverse, viewname=self.detail_view_name, request=request)
        repo_config = {'url_builder': url_builder}
        service_delivery = self.repo_class(config=repo_config).upsert(data)

        return Response(service_delivery)


class ServiceDeliveryDetailViewV2(APIView):
    """Service delivery detail view."""

    repo_class = service_deliveries_repos.ServiceDeliveryDatabaseRepo
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    parser_classes = (JSONParser, parsers.FormParser, parsers.MultiPartParser)
    detail_view_name = 'v2:servicedelivery-detail'
    entity_name = 'ServiceDelivery'

    def get(self, request, object_id):
        """Handle the GET."""
        url_builder = functools.partial(
            reverse, viewname=self.detail_view_name, request=request)
        repo_config = {'url_builder': url_builder}
        service_delivery = self.repo_class(config=repo_config).get(object_id=object_id)
        return Response(service_delivery)

    def post(self, request):
        """Handle the POST."""
        return self.upsert(request)

    def patch(self, request, object_id):
        """Handle the PATCH."""
        return self.upsert(request)

    def upsert(self, request):
        """Perform upsert POST and PATCH."""
        data = dict(request.data)
        url_builder = functools.partial(
            reverse, viewname=self.detail_view_name, request=request)
        repo_config = {'url_builder': url_builder}
        service_delivery = self.repo_class(config=repo_config).upsert(data)

        return Response(service_delivery)
