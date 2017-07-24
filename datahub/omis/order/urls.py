"""Company views URL config."""

from django.conf.urls import url

from .views import OrderViewSet, SubscriberListView


order_collection = OrderViewSet.as_view({
    'post': 'create'
})

order_item = OrderViewSet.as_view({
    'get': 'retrieve'
})


urlpatterns = [
    url(r'^order$', order_collection, name='list'),
    url(r'^order/(?P<pk>[0-9a-z-]{36})$', order_item, name='detail'),

    url(
        r'^order/(?P<order_pk>[0-9a-z-]{36})/subscriber-list$',
        SubscriberListView.as_view(),
        name='subscriber-list'
    ),
]
