from django.urls import path

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
    path('interaction', collection, name='collection'),
    path('interaction/<uuid:pk>', item, name='item'),
]
