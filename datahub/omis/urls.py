from django.conf.urls import include, url

from .invoice import urls as invoice_urls
from .order import urls as order_urls
from .quote import urls as quote_urls

internal_frontend_urls = [
    url(r'^', include((order_urls.internal_frontend_urls, 'order'), namespace='order')),
    url(r'^', include((quote_urls.internal_frontend_urls, 'quote'), namespace='quote')),
    url(r'^', include((invoice_urls.internal_frontend_urls, 'invoice'), namespace='invoice')),
]

public_urls = [
    url(r'^', include((order_urls.public_urls, 'order'), namespace='order')),
    url(r'^', include((quote_urls.public_urls, 'quote'), namespace='quote')),
    url(r'^', include((invoice_urls.public_urls, 'invoice'), namespace='invoice')),
]
