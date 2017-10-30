"""Company views URL config."""

from django.conf.urls import url

from .views import AssigneeView, OrderViewSet, PublicOrderViewSet, SubscriberListView

# internal frontend API
internal_frontend_urls = [
    url(r'^order$', OrderViewSet.as_view({'post': 'create'}), name='list'),
    url(
        r'^order/(?P<pk>[0-9a-z-]{36})$',
        OrderViewSet.as_view({
            'get': 'retrieve',
            'patch': 'partial_update'
        }),
        name='detail'
    ),
    url(
        r'^order/(?P<pk>[0-9a-z-]{36})/complete$',
        OrderViewSet.as_view({'post': 'complete'}),
        name='complete'
    ),

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
public_urls = [
    url(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})$',
        PublicOrderViewSet.as_view({'get': 'retrieve'}),
        name='detail'
    ),
]
