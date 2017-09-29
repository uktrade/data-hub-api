from django.conf.urls import include, url

from .order import urls as order_urls
from .quote import urls as quote_urls

internal_frontend_urls = [
    url(r'^', include((order_urls.internal_frontend_urls, 'order'), namespace='order')),
    url(r'^', include((quote_urls.internal_frontend_urls, 'quote'), namespace='quote')),
]

public_urls = [
    url(r'^', include((order_urls.public_urls, 'order'), namespace='order')),
    url(r'^', include((quote_urls.public_urls, 'quote'), namespace='quote')),
]
