"""Company views URL config."""

from django.conf.urls import url

from .views import OrderViewSet


order_collection = OrderViewSet.as_view({
    'post': 'create'
})

urlpatterns = [
    url(r'^order$', order_collection, name='list'),
]
