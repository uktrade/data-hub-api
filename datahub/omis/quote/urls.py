from django.conf.urls import url

from .views import PublicQuoteViewSet, QuoteViewSet


# internal frontend API
internal_frontend_urls = [
    url(
        r'^order/(?P<order_pk>[0-9a-z-]{36})/quote$',
        QuoteViewSet.as_view({
            'post': 'create',
            'get': 'retrieve',
        }),
        name='detail'
    ),
    url(
        r'^order/(?P<order_pk>[0-9a-z-]{36})/quote/preview$',
        QuoteViewSet.as_view({'post': 'preview'}),
        name='preview'
    ),
    url(
        r'^order/(?P<order_pk>[0-9a-z-]{36})/quote/cancel$',
        QuoteViewSet.as_view({'post': 'cancel'}),
        name='cancel'
    ),
]

# public facing API
public_urls = [
    url(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/quote$',
        PublicQuoteViewSet.as_view({'get': 'retrieve'}),
        name='detail'
    ),
    url(
        r'^order/(?P<public_token>[0-9A-Za-z_\-]{50})/quote/accept$',
        PublicQuoteViewSet.as_view({'post': 'accept'}),
        name='accept'
    ),
]
