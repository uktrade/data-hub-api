from django.urls import include, path

from datahub.omis.invoice import urls as invoice_urls
from datahub.omis.order import urls as order_urls
from datahub.omis.payment import urls as payment_urls
from datahub.omis.quote import urls as quote_urls

internal_frontend_urls = [
    path('', include((order_urls.internal_frontend_urls, 'order'), namespace='order')),
    path('', include((quote_urls.internal_frontend_urls, 'quote'), namespace='quote')),
    path('', include((invoice_urls.internal_frontend_urls, 'invoice'), namespace='invoice')),
    path(
        '',
        include(
            (payment_urls.payment_internal_frontend_urls, 'payment'), namespace='payment',
        ),
    ),
]

public_urls = [
    path('', include((order_urls.legacy_public_urls, 'order'), namespace='order')),
    path('', include((quote_urls.legacy_public_urls, 'quote'), namespace='quote')),
    path('', include((payment_urls.payment_public_urls, 'payment'), namespace='payment')),
    path(
        '',
        include(
            (payment_urls.legacy_payment_gateway_session_public_urls, 'payment-gateway-session'),
            namespace='payment-gateway-session',
        ),
    ),
    path('', include((invoice_urls.legacy_public_urls, 'invoice'), namespace='invoice')),
]

# TODO: rename this to public_urls once all public urls have been migrated to Hawk
hawk_public_urls = [
    path('', include((order_urls.hawk_public_urls, 'order'), namespace='order')),
    path('', include((quote_urls.hawk_public_urls, 'quote'), namespace='quote')),
    path(
        '',
        include(
            (payment_urls.hawk_payment_gateway_session_public_urls, 'payment-gateway-session'),
            namespace='payment-gateway-session',
        ),
    ),
    path('', include((invoice_urls.hawk_public_urls, 'invoice'), namespace='invoice')),
]
