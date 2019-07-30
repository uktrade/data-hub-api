from django.urls import path

from datahub.user.company_list.views import CompanyListItemView, CompanyListViewSet

urlpatterns = [
    path(
        'user/company-list',
        CompanyListViewSet.as_view(
            {
                'get': 'list',
            },
        ),
        name='collection',
    ),
    path(
        'user/company-list/<uuid:company_pk>',
        CompanyListItemView.as_view(),
        name='item',
    ),
]
