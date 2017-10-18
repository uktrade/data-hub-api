from django.conf.urls import url

from .views import PaymentViewSet, PublicPaymentViewSet


# internal frontend API
internal_frontend_urls = [
    url(
        r'^order/(?P<order_pk>[0-9a-z-]{36})/payment$',
        PaymentViewSet.as_view({
            'get': 'list',
            'post': 'create_list'
        }),
        name='collection'
    ),
]

# public facing API
public_urls = [
    url(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/payment$',
        PublicPaymentViewSet.as_view({'get': 'list'}),
        name='collection'
    ),
]
