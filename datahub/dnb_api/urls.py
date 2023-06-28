from django.urls import path

from datahub.dnb_api.views import (
    DNBCompanyChangeRequestView,
    DNBCompanyCreateView,
    DNBCompanyHierarchyView,
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
    path(
        '<company_id>/family-tree',
        DNBCompanyHierarchyView.as_view(),
        name='family-tree',
    ),
    path(
        '<company_id>/related-companies/count',
        DNBCompanyHierarchyView.as_view(),
        name='family-tree',
    ),
]
