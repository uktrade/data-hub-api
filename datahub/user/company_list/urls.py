from django.urls import path

from datahub.user.company_list.views import CompanyListItemView

urlpatterns = [
    path(
        'user/company-list/<uuid:company_pk>',
        CompanyListItemView.as_view(),
        name='item',
    ),
]
