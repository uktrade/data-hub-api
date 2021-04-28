from django.urls import path

from datahub.interaction.views import InteractionViewSet, InteractionViewSetV4

collection = InteractionViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

item = InteractionViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

archive_item = InteractionViewSet.as_action_view('archive')

unarchive_item = InteractionViewSet.as_action_view('unarchive')

urls_v3 = [
    path('interaction', collection, name='collection'),
    path('interaction/<uuid:pk>', item, name='item'),
    path(
        'interaction/<uuid:pk>/archive',
        archive_item,
        name='archive-item',
    ),
    path(
        'interaction/<uuid:pk>/unarchive',
        unarchive_item,
        name='unarchive-item',
    ),
]

collection_v4 = InteractionViewSetV4.as_view({
    'get': 'list',
    'post': 'create',
})

item_v4 = InteractionViewSetV4.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

archive_item_v4 = InteractionViewSetV4.as_action_view('archive')

unarchive_item_v4 = InteractionViewSetV4.as_action_view('unarchive')

urls_v4 = [
    path('interaction', collection_v4, name='collection'),
    path('interaction/<uuid:pk>', item_v4, name='item'),
    path(
        'interaction/<uuid:pk>/archive',
        archive_item_v4,
        name='archive-item',
    ),
    path(
        'interaction/<uuid:pk>/unarchive',
        unarchive_item_v4,
        name='unarchive-item',
    ),
]
