from django.conf.urls import url

from datahub.interaction.views import InteractionViewSetV3

collection = InteractionViewSetV3.as_view({
    'get': 'list',
    'post': 'create'
})

item = InteractionViewSetV3.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

urlpatterns = [
    url(r'^interaction$', collection, name='collection'),
    url(r'^interaction/(?P<pk>[0-9a-z-]{36})$', item, name='item'),
]
