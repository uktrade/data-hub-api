from django.urls import path

from datahub.user.company_list.legacy_views import (
    LegacyCompanyListItemView,
    LegacyCompanyListViewSet,
)

urlpatterns = [
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
