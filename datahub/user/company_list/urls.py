from django.urls import path

from datahub.user.company_list.legacy_views import (
    LegacyCompanyListItemView,
    LegacyCompanyListViewSet,
)
from datahub.user.company_list.views import CompanyListViewSet

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
                'patch': 'partial_update',
            },
        ),
        name='list-detail',
    ),
    path(
        'user/company-list',
        LegacyCompanyListViewSet.as_view(
            {
                'get': 'list',
            },
        ),
        name='collection',
    ),
    path(
        'user/company-list/<uuid:company_pk>',
        LegacyCompanyListItemView.as_view(),
        name='item',
    ),
]
