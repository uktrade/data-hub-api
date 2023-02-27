from django.urls import path

from datahub.company.views import CompanyExportViewSet

export_v4_collection = CompanyExportViewSet.as_view(
    {
        'post': 'create',
    },
)

urls_v4 = [
    path(
        'export',
        export_v4_collection,
        name='collection',
    ),
]
