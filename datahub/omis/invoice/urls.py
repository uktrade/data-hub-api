from django.conf.urls import url

from .views import InvoiceViewSet, PublicInvoiceViewSet


# internal frontend API
internal_frontend_urls = [
    url(
        r'^order/(?P<order_pk>[0-9a-z-]{36})/invoice$',
        InvoiceViewSet.as_view({'get': 'retrieve'}),
        name='detail'
    ),
]

# public facing API
public_urls = [
    url(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/invoice$',
        PublicInvoiceViewSet.as_view({'get': 'retrieve'}),
        name='detail'
    ),
]
