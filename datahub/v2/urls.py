from django.conf.urls import url

from datahub.v2.views import service_deliveries as service_deliveries_views

urlpatterns = [
    url(
        r'^service_delivery/$',
        service_deliveries_views.ServiceDeliveryListViewV2.as_view(),
        name='servicedelivery-list'),
    url(
        r'^service_delivery/(?P<object_id>[0-9a-z-]{36})/$',
        service_deliveries_views.ServiceDeliveryDetailViewV2.as_view(),
        name='servicedelivery-detail'),
]
