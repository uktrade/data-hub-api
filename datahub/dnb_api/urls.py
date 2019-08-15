from django.urls import path

from datahub.dnb_api.views import DNBCompanyCreateView, DNBCompanySearchView

urlpatterns = [
    path(
        'company-search',
        DNBCompanySearchView.as_view(),
        name='company-search',
    ),
    path(
        'company-create',
        DNBCompanyCreateView.as_view(),
        name='company-create',
    ),
]
