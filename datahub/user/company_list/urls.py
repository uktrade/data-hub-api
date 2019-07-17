from django.urls import path

from datahub.user.company_list.views import CreateOrUpdateCompanyListItemView

urlpatterns = [
    path(
        'user/company-list/<uuid:company_pk>',
        CreateOrUpdateCompanyListItemView.as_view(),
        name='replace-item',
    ),
]
