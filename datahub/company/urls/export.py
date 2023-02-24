from django.urls import path

from datahub.company.views import CompanyExportViewSet

urlpatterns = [
    path(
        'exports',
        CompanyExportViewSet.as_view(
            {
                'get': 'list',
                'post': 'create',
            },
        ),
        name='list',
    ),
    path(
        'exports/<uuid:pk>',
        CompanyExportViewSet.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
                'delete': 'destroy',
            },
        ),
        name='item',
    ),
]
