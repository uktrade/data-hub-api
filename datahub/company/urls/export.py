from django.urls import path

from datahub.company.views import CompanyExportViewSet

export_v4_collection = CompanyExportViewSet.as_view(
    {
        'get': 'list',
        'post': 'create',
    },
)
export_v4_item = CompanyExportViewSet.as_view(
    {'get': 'retrieve', 'patch': 'partial_update'},
)

urls_v4 = [
    path(
        'export',
        export_v4_collection,
        name='collection',
    ),
    path(
        'export/<uuid:pk>',
        export_v4_item,
        name='item',
    ),
]
