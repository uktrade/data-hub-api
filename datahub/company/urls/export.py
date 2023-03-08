from django.urls import path

from datahub.company.views import CompanyExportViewSet

export_v4_item = CompanyExportViewSet.as_view(
    {
        'get': 'retrieve',
    },
)

urls_v4 = [
    path(
        'export/<uuid:pk>',
        export_v4_item,
        name='item',
    ),
]
