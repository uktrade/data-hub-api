from django.urls import path

from datahub.event.views import EventViewSetV4

collectionv4 = EventViewSetV4.as_view({
    'get': 'list',
    'post': 'create',
})

itemv4 = EventViewSetV4.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

urlpatterns = [
    path('event', collectionv4, name='collectionv4'),
    path('event/<uuid:pk>', itemv4, name='itemv4'),
]
