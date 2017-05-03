"""Search views URL config."""

from django.conf.urls import url

from datahub.search.views import (
    SearchBasicAPIView, SearchCompanyAPIView, SearchContactAPIView
)

urlpatterns = [
    url(r'^$', SearchBasicAPIView.as_view(), name='basic'),
    url(r'^company/$', SearchCompanyAPIView.as_view(), name='company'),
    url(r'^contact/$', SearchContactAPIView.as_view(), name='contact'),
]
