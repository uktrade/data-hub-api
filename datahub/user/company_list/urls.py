from django.urls import path

from datahub.user.company_list.legacy_views import (
    LegacyCompanyListItemView,
    LegacyCompanyListViewSet,
)
from datahub.user.company_list.views import (
    CompanyListItemAPIView,
    CompanyListItemViewSet,
)


urlpatterns = [
    path(
        'company-list/<uuid:company_list_pk>/<uuid:company_pk>',
        CompanyListItemAPIView.as_view(),
        name='list-item',
    ),
    path(
        'company-list/<uuid:company_list_pk>',
        CompanyListItemViewSet.as_view(
            {
                'get': 'list',
            },
        ),
        name='list-collection',
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
