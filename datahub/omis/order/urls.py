"""Company views URL config."""

from django.conf.urls import url

from .views import AssigneeView, OrderViewSet, PublicOrderViewSet, SubscriberListView

# internal frontend API
order_collection = OrderViewSet.as_view({
    'post': 'create'
})

order_item = OrderViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})


internal_frontend_urls = [
    url(r'^order$', order_collection, name='list'),
    url(r'^order/(?P<pk>[0-9a-z-]{36})$', order_item, name='detail'),

    url(
        r'^order/(?P<order_pk>[0-9a-z-]{36})/subscriber-list$',
        SubscriberListView.as_view(),
        name='subscriber-list'
    ),

    url(
        r'^order/(?P<order_pk>[0-9a-z-]{36})/assignee$',
        AssigneeView.as_view(),
        name='assignee'
    ),
]


# public facing API
public_order_item = PublicOrderViewSet.as_view({
    'get': 'retrieve'
})

public_urls = [
    url(r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})$', public_order_item, name='detail'),
]
