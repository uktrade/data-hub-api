from django.urls import path

from datahub.dnb_api.views import (
    DNBCompanyChangeRequestView,
    DNBCompanyCreateView,
    DNBCompanyInvestigationView,
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
        'company-link',
        DNBCompanyLinkView.as_view(),
        name='company-link',
    ),
    path(
        'company-change-request',
        DNBCompanyChangeRequestView.as_view(),
        name='company-change-request',
    ),
    path(
        'company-investigation',
        DNBCompanyInvestigationView.as_view(),
        name='company-investigation',
    ),
]
