from django.urls import path

from datahub.dnb_api.views import DNBCompanySearchView

urlpatterns = [
    path(
        'company-search',
        DNBCompanySearchView.as_view(),
        name='company-search',
    ),
]
