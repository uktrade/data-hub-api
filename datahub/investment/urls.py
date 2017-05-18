"""Investment views URL config."""

from django.conf.urls import url

from datahub.investment.views import (
    IProjectRequirementsViewSet, IProjectTeamViewSet, IProjectValueViewSet,
    IProjectViewSet
)

project_collection = IProjectViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

project_item = IProjectViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

value_item = IProjectValueViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

requirements_item = IProjectRequirementsViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

team_item = IProjectTeamViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

urlpatterns = [
    url(r'^project$', project_collection, name='project'),
    url(r'^(?P<pk>[0-9a-z-]{36})/project$', project_item, name='project-item'),
    url(r'^(?P<pk>[0-9a-z-]{36})/value$', value_item, name='value-item'),
    url(r'^(?P<pk>[0-9a-z-]{36})/requirements$', requirements_item, name='requirements-item'),
    url(r'^(?P<pk>[0-9a-z-]{36})/team', team_item, name='team-item')
]
