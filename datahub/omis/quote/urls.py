from django.urls import path, re_path

from datahub.omis.quote.views import PublicQuoteViewSet, QuoteViewSet

# internal frontend API
internal_frontend_urls = [
    path(
        'order/<uuid:order_pk>/quote',
        QuoteViewSet.as_view({
            'post': 'create',
            'get': 'retrieve',
        }),
        name='detail',
    ),
    path(
        'order/<uuid:order_pk>/quote/preview',
        QuoteViewSet.as_view({'post': 'preview'}),
        name='preview',
    ),
    path(
        'order/<uuid:order_pk>/quote/cancel',
        QuoteViewSet.as_view({'post': 'cancel'}),
        name='cancel',
    ),
]

# Hawk authenticated public facing API
public_urls = [
    re_path(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/quote$',
        PublicQuoteViewSet.as_view({'get': 'retrieve'}),
        name='detail',
    ),
    re_path(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/quote/accept$',
        PublicQuoteViewSet.as_view({'post': 'accept'}),
        name='accept',
    ),
]
