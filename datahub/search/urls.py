"""Search views URL config."""

from django.conf.urls import url

from datahub.search.views import (
    SearchBasicAPIView, SearchCompanyAPIView, SearchContactAPIView,
    SearchInvestmentProjectAPIView
)

urlpatterns = [
    url(r'^search$', SearchBasicAPIView.as_view(), name='basic'),
    url(r'^search/company$', SearchCompanyAPIView.as_view(), name='company'),
    url(r'^search/contact$', SearchContactAPIView.as_view(), name='contact'),
    url(r'^search/investment_project$',
        SearchInvestmentProjectAPIView.as_view(),
        name='investment_project'
        )
]
