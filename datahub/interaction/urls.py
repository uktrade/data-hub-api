from django.conf.urls import url

from datahub.interaction.views import InteractionViewSet

collection = InteractionViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

item = InteractionViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

urlpatterns = [
    url(r'^interaction$', collection, name='collection'),
    url(r'^interaction/(?P<pk>[0-9a-z-]{36})$', item, name='item'),
]
