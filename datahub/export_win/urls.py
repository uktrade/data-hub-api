from django.urls import path

from datahub.export_win.views import (
    CustomerResponseViewSet,
    WinViewSet,
)

win_collection = WinViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

win_item = WinViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

resend_export_win = WinViewSet.as_action_view(
    'resend_export_win',
)

customer_response = CustomerResponseViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

urls = [
    path('export-win', win_collection, name='collection'),
    path('export-win/<uuid:pk>', win_item, name='item'),
    path('export-win/review/<uuid:token_pk>', customer_response, name='customer-response'),
    path('export-win/<uuid:pk>/resend-win', resend_export_win, name='win-resend'),
]
