from django.urls import path

from datahub.export_win.views import WinViewSet

collection = WinViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

item = WinViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

urls = [
    path('export_win', collection, name='collection'),
    path('export_win/<uuid:pk>', item, name='item'),
]
