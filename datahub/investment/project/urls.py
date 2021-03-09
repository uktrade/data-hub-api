"""Investment views URL config."""

from django.urls import include, path

from datahub.investment.project.evidence.urls import urlpatterns as evidence_urlpatterns
from datahub.investment.project.proposition.urls import urls_v3 as proposition_urlpatterns
from datahub.investment.project.views import (
    IProjectAuditViewSet,
    IProjectTeamMembersViewSet,
    IProjectViewSet,
)

project_collection = IProjectViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

project_item = IProjectViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

project_team_member_collection = IProjectTeamMembersViewSet.as_view({
    'post': 'create',
    'delete': 'destroy_all',
    'put': 'replace_all',
})

project_team_member_item = IProjectTeamMembersViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy',
})

audit_item = IProjectAuditViewSet.as_view({
    'get': 'list',
})

archive_item = IProjectViewSet.as_action_view('archive')

unarchive_item = IProjectViewSet.as_action_view('unarchive')

update_stage_of_item = IProjectViewSet.as_action_view('change_stage')


urlpatterns = [
    path(
        'investment',
        project_collection,
        name='investment-collection',
    ),
    path(
        'investment/<uuid:pk>',
        project_item,
        name='investment-item',
    ),
    path(
        'investment/<uuid:pk>/archive',
        archive_item,
        name='archive-item',
    ),
    path(
        'investment/<uuid:project_pk>/team-member',
        project_team_member_collection,
        name='team-member-collection',
    ),
    path(
        'investment/<uuid:project_pk>/team-member/<uuid:adviser_pk>',
        project_team_member_item,
        name='team-member-item',
    ),
    path(
        'investment/<uuid:pk>/unarchive',
        unarchive_item,
        name='unarchive-item',
    ),
    path(
        'investment/<uuid:pk>/audit',
        audit_item,
        name='audit-item',
    ),
    path(
        'investment/<uuid:pk>/update-stage',
        update_stage_of_item,
        name='update-stage-of-item',
    ),
    path(
        'investment/<uuid:project_pk>/',
        include(
            (proposition_urlpatterns, 'proposition'),
            namespace='proposition',
        ),
    ),
    path(
        'investment/<uuid:project_pk>/',
        include(
            (evidence_urlpatterns, 'evidence-document'),
            namespace='evidence-document',
        ),
    ),
]
