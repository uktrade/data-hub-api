from django.conf.urls import include, url

from .order import urls as order_urls
from .quote import urls as quote_urls

urlpatterns = [
    url(r'^', include((order_urls, 'order'), namespace='order')),
    url(r'^', include((quote_urls, 'quote'), namespace='quote')),
]
