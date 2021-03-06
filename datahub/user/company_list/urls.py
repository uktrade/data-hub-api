from django.urls import path

from datahub.user.company_list.views import (
    CompanyListItemAPIView,
    CompanyListItemViewSet,
    CompanyListViewSet,
    PipelineItemViewSet,
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
        PipelineItemViewSet.as_view(
            {
                'get': 'list',
                'post': 'create',
            },
        ),
        name='pipelineitem-collection',
    ),
    path(
        'pipeline-item/<uuid:pk>',
        PipelineItemViewSet.as_view(
            {
                'patch': 'partial_update',
                'get': 'retrieve',
                'delete': 'destroy',
            },
        ),
        name='pipelineitem-detail',
    ),
    path(
        'pipeline-item/<uuid:pk>/archive',
        PipelineItemViewSet.as_action_view(
            'archive',
        ),
        name='pipelineitem-archive',
    ),
    path(
        'pipeline-item/<uuid:pk>/unarchive',
        PipelineItemViewSet.as_action_view(
            'unarchive',
        ),
        name='pipelineitem-unarchive',
    ),
]
