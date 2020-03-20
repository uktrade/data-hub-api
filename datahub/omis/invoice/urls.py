from django.urls import path, re_path

from datahub.omis.invoice.legacy_public_views import LegacyPublicInvoiceViewSet
from datahub.omis.invoice.views import InvoiceViewSet, PublicInvoiceViewSet

# internal frontend API
internal_frontend_urls = [
    path(
        'order/<uuid:order_pk>/invoice',
        InvoiceViewSet.as_view({'get': 'retrieve'}),
        name='detail',
    ),
]

# legacy public facing API
legacy_public_urls = [
    re_path(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/invoice$',
        LegacyPublicInvoiceViewSet.as_view({'get': 'retrieve'}),
        name='detail',
    ),
]

# Hawk authenticated public facing API
hawk_public_urls = [
    re_path(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/invoice$',
        PublicInvoiceViewSet.as_view({'get': 'retrieve'}),
        name='detail',
    ),
]
