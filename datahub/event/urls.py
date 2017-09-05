from django.conf.urls import url

from datahub.event.views import EventViewSet

collection = EventViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

item = EventViewSet.as_view({
    'get': 'retrieve',
})

urlpatterns = [
    url(r'^event$', collection, name='collection'),
    url(r'^event/(?P<pk>[0-9a-z-]{36})$', item, name='item'),
]
