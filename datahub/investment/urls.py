from django.conf.urls import include, url

from datahub.investment.views import (
    InvestmentProjectViewSet, InvestmentProjectValueViewSet
)

app_name = 'investment'

project_collection = InvestmentProjectViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

project_item = InvestmentProjectViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

value_item = InvestmentProjectValueViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

urlpatterns_v3 = [
    url(r'^investment/project$', project_collection, name='project'),
    url(r'^investment/(?P<pk>[0-9a-z-]{36})/project$', project_item,
        name='project-item'),
    url(r'^investment/(?P<pk>[0-9a-z-]{36})/value$', value_item,
        name='value-item')
]

urlpatterns = [
    url('^v3/', include(urlpatterns_v3, namespace='v3'))
]
