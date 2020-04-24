"""Company views URL config."""

from django.urls import path, re_path

from datahub.omis.order.views import (
    AssigneeView,
    OrderViewSet,
    PublicOrderViewSet,
    SubscriberListView,
)

# internal frontend API
internal_frontend_urls = [
    path('order', OrderViewSet.as_view({'post': 'create'}), name='list'),
    path(
        'order/<uuid:pk>',
        OrderViewSet.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
        }),
        name='detail',
    ),
    path(
        'order/<uuid:pk>/complete',
        OrderViewSet.as_action_view('complete'),
        name='complete',
    ),
    path(
        'order/<uuid:pk>/cancel',
        OrderViewSet.as_action_view('cancel'),
        name='cancel',
    ),

    path(
        'order/<uuid:order_pk>/subscriber-list',
        SubscriberListView.as_view(),
        name='subscriber-list',
    ),

    path(
        'order/<uuid:order_pk>/assignee',
        AssigneeView.as_view(),
        name='assignee',
    ),
]


# Hawk authenticated public facing API
public_urls = [
    re_path(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})$',
        PublicOrderViewSet.as_view({'get': 'retrieve'}),
        name='detail',
    ),
]
