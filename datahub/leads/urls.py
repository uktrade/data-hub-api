"""Investment views URL config."""

from django.conf.urls import url

from datahub.leads.views import BusinessLeadViewSet

lead_collection = BusinessLeadViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

lead_item = BusinessLeadViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

urlpatterns = [
    url(r'^business-leads$', lead_collection, name='lead-collection'),
    url(r'^business-leads/(?P<pk>[0-9a-z-]{36})$', lead_item, name='lead-item')
]
