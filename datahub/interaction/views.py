from collections import OrderedDict

from django_filters import CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework.views import APIView
import rest_framework_json_api
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from datahub.core.viewsets import CoreViewSetV1
from datahub.interaction.models import Interaction, ServiceDelivery
from datahub.interaction.serializers import (
    InteractionSerializerRead,
    InteractionSerializerWrite,
)
from datahub.v2 import repos


class InteractionViewSetV1(CoreViewSetV1):
    """Interaction ViewSet."""

    read_serializer_class = InteractionSerializerRead
    write_serializer_class = InteractionSerializerWrite
    queryset = Interaction.objects.select_related(
        'interaction_type',
        'dit_advisor',
        'company',
        'contact'
    ).all()

    def create(self, request, *args, **kwargs):
        """Override create to inject the user from session."""
        request.data.update({'dit_advisor': str(request.user.pk)})
        return super().create(request, *args, **kwargs)


class ServiceDeliveryFilter(FilterSet):
    """Service delivery filter."""

    company = CharFilter(name='company__pk', lookup_expr='exact')
    contact = CharFilter(name='contact__pk', lookup_expr='exact')

    class Meta:  # noqa: D101
        model = ServiceDelivery
        fields = ['company', 'contact']


class ServiceDeliveryListViewV2(APIView):
    """Service delivery list view."""

    repo_class = repos.service_deliveries.ServiceDeliveryDatabaseRepo
    param_keys = frozenset({'company_id', 'contact_id', 'offset', 'limit'})
    renderer_classes = (
        rest_framework_json_api.renderers.JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        params = {k: v for (k, v) in request.query_params.items() if k in self.param_keys}
        service_deliveries = self.repo_class().filter(**params)
        return Response(service_deliveries)

    def post(self, request):
        data = dict(request.data)
        data.update({
            'dit_advisor': OrderedDict([
                ('type', 'Advisor'), ('id', str(request.user.pk))])})
        service_delivery = self.repo_class().upsert(data)
        return Response(service_delivery)


class ServiceDeliveryDetailViewV2(APIView):
    """Service delivery detail view."""

    repo_class = ServiceDeliveryDatabaseRepo
    renderer_classes = (
        rest_framework_json_api.renderers.JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, object_id):
        service_delivery = self.repo_class().get(object_id=object_id)
        return Response(service_delivery)

    def post(self, request, object_id):
        data = dict(request.data)
        service_delivery = self.repo_class().upsert(data)
        return Response(service_delivery)
