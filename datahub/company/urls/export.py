from django.urls import path

from datahub.company.views import CompanyExportViewSet

urlpatterns = [
    path(
        'exports',
        CompanyExportViewSet.as_view(
            {
                'get': 'list',
            },
        ),
        name='list',
    ),
]
