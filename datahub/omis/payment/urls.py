from django.urls import path, re_path

from .views import PaymentViewSet, PublicPaymentViewSet


# internal frontend API
internal_frontend_urls = [
    path(
        'order/<uuid:order_pk>/payment',
        PaymentViewSet.as_view({
            'get': 'list',
            'post': 'create_list'
        }),
        name='collection'
    ),
]

# public facing API
public_urls = [
    re_path(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/payment$',
        PublicPaymentViewSet.as_view({'get': 'list'}),
        name='collection'
    ),
]
