from django.conf.urls import include, url

from .order import urls as order_urls

urlpatterns = [
    url(r'^', include((order_urls, 'order'), namespace='order')),
]
