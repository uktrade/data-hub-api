from django.urls import path

from datahub.user.company_list.legacy_views import (
    LegacyCompanyListItemView,
    LegacyCompanyListViewSet,
)
from datahub.user.company_list.views import (
    CompanyListItemAPIView,
    CompanyListItemViewSet,
    CompanyListViewSet,
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
