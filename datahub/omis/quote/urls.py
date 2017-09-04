from django.conf.urls import url

from .views import QuoteViewSet


urlpatterns = [
    url(
        r'^order/(?P<order_pk>[0-9a-z-]{36})/quote$',
        QuoteViewSet.as_view({
            'post': 'create',
            'get': 'retrieve',
        }),
        name='item'
    ),
]
