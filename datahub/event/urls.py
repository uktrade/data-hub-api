from django.urls import path

from datahub.event.views import EventViewSet

collection = EventViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

item = EventViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

urlpatterns = [
    path('event', collection, name='collection'),
    path('event/<uuid:pk>', item, name='item'),
]
