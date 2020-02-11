from django.urls import path

from datahub.dnb_api.views import (
    DNBCompanyCreateInvestigationView,
    DNBCompanyCreateView,
    DNBCompanyLinkView,
    DNBCompanySearchView,
)

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
    path(
        'company-create-investigation',
        DNBCompanyCreateInvestigationView.as_view(),
        name='company-create-investigation',
    ),
    path(
        'company-link',
        DNBCompanyLinkView.as_view(),
        name='company-link',
    ),
]
