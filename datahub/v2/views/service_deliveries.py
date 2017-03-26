from collections import OrderedDict

from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.v2.renderers import JSONRenderer
from datahub.v2.repos import service_deliveries as service_deliveries_repos


class ServiceDeliveryListViewV2(APIView):
    """Service delivery list view."""

    repo_class = service_deliveries_repos.ServiceDeliveryDatabaseRepo
    param_keys = frozenset({'company_id', 'contact_id', 'offset', 'limit'})
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        params = {k: v for (k, v) in request.query_params.items() if k in self.param_keys}
        repo_config = {'request': request}
        service_deliveries = self.repo_class(config=repo_config).filter(**params)
        return Response(service_deliveries)

    def post(self, request):
        data = dict(request.data)
        data.update({
            'dit_advisor': OrderedDict([
                ('type', 'Advisor'), ('id', str(request.user.pk))])})
        repo_config = {'request': request}
        service_delivery = self.repo_class(config=repo_config).upsert(data)
        return Response(service_delivery)


class ServiceDeliveryDetailViewV2(APIView):
    """Service delivery detail view."""

    repo_class = service_deliveries_repos.ServiceDeliveryDatabaseRepo
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, object_id):
        repo_config = {'request': request}
        service_delivery = self.repo_class(config=repo_config).get(object_id=object_id)
        return Response(service_delivery)

    def post(self, request, object_id):
        data = dict(request.data)
        repo_config = {'request': request}
        service_delivery = self.repo_class(config=repo_config).upsert(data)
        return Response(service_delivery)
