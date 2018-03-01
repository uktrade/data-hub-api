from django.urls import path, re_path

from .views import PaymentViewSet, PublicPaymentGatewaySessionViewSet, PublicPaymentViewSet


# internal frontend API
payment_internal_frontend_urls = [
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
payment_public_urls = [
    re_path(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/payment$',
        PublicPaymentViewSet.as_view({'get': 'list'}),
        name='collection'
    ),
]

payment_gateway_session_public_urls = [
    re_path(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/payment-gateway-session$',
        PublicPaymentGatewaySessionViewSet.as_view({'post': 'create'}),
        name='collection'
    ),
]
