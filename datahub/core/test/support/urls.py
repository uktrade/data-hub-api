from django.urls import path

from datahub.core.test.support.views import (
    HawkViewWithoutScope,
    HawkViewWithScope,
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
        'test-hawk-without-scope/',
        HawkViewWithoutScope.as_view(),
        name='test-hawk-without-scope',
    ),
    path(
        'test-hawk-with-scope/',
        HawkViewWithScope.as_view(),
        name='test-hawk-with-scope',
    ),
]
