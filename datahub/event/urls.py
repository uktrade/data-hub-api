from django.urls import path

from datahub.event.views import EventViewSet, EventViewSetV4

collection = EventViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

item = EventViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

urls_v3 = [
    path('event', collection, name='collection'),
    path('event/<uuid:pk>', item, name='item'),
]

collectionv4 = EventViewSetV4.as_view({
    'get': 'list',
    'post': 'create',
})

itemv4 = EventViewSetV4.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

urls_v4 = [
    path('event', collectionv4, name='collection'),
    path('event/<uuid:pk>', itemv4, name='item'),
]
