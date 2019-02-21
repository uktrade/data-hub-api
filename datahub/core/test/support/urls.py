from django.urls import path

from datahub.core.test.support.views import (
    HawkView,
    MultiAddressModelViewset,
    MyDisableableModelViewset,
)

urlpatterns = [
    path(
        'test-disableable/',
        MyDisableableModelViewset.as_view({
            'get': 'list',
        }),
        name='test-disableable-collection',
    ),
    path(
        'test-addresses/',
        MultiAddressModelViewset.as_view({
            'get': 'list',
            'post': 'create',
        }),
        name='test-addresses-collection',
    ),
    path(
        'test-addresses/<int:pk>/',
        MultiAddressModelViewset.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
        }),
        name='test-addresses-item',
    ),
    path(
        'test-hawk/',
        HawkView.as_view(),
        name='test-hawk',
    ),
]
