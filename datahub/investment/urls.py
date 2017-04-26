from django.conf.urls import include, url

from datahub.investment.views import InvestmentProjectViewSet

app_name = 'investment'

project_collection = InvestmentProjectViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

project_item = InvestmentProjectViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

urlpatterns_v3 = [
    url(r'^investment/project$', project_collection, name='project'),
    url(r'^investment/project/(?P<pk>[0-9a-z-]{36})$', project_item,
        name='project-item')
]

urlpatterns = [
    url('^v3/', include(urlpatterns_v3, namespace='v3'))
]
