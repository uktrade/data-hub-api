from django.urls import path

from datahub.user.company_list.views import (
    CompanyListItemAPIView,
    CompanyListItemViewSet,
    CompanyListViewSet,
    ExportPipelineItemViewSet,
)

urlpatterns = [
    path(
        'company-list',
        CompanyListViewSet.as_view(
            {
                'get': 'list',
                'post': 'create',
            },
        ),
        name='list-collection',
    ),
    path(
        'company-list/<uuid:pk>',
        CompanyListViewSet.as_view(
            {
                'delete': 'destroy',
                'get': 'retrieve',
                'patch': 'partial_update',
            },
        ),
        name='list-detail',
    ),
    path(
        'company-list/<uuid:company_list_pk>/item',
        CompanyListItemViewSet.as_view(
            {
                'get': 'list',
            },
        ),
        name='item-collection',
    ),
    path(
        'company-list/<uuid:company_list_pk>/item/<uuid:company_pk>',
        CompanyListItemAPIView.as_view(),
        name='item-detail',
    ),
    path(
        'pipeline-item',
        ExportPipelineItemViewSet.as_view(
            {
                'get': 'list',
            },
        ),
        name='pipelineitem-collection',
    ),
]
