from django.urls import path

from datahub.core.test.support.views import (
    HawkViewWithoutScope,
    HawkViewWithScope,
    max_upload_size_view,
    MultiAddressModelViewset,
    MyDisableableModelViewset,
    PaasIPView,
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
    path(
        'test-paas-ip/',
        PaasIPView.as_view(),
        name='test-paas-ip',
    ),
    path(
        'test-max-upload-size/',
        max_upload_size_view,
        name='test-max-upload-size',
    ),
]
