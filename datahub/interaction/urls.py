from django.urls import path

from datahub.interaction.views import InteractionViewSet, MailViewSet

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

urlpatterns = [
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
    path(
        'interaction/mail',
        MailViewSet.as_view(),
        name='mail',
    ),
]
