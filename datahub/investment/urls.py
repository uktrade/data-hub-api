"""Investment views URL config."""

from django.urls import include, path

from datahub.investment.proposition import urls as proposition_urls
from datahub.investment.views import (
    IProjectAuditViewSet, IProjectDocumentViewSet, IProjectModifiedSinceViewSet,
    IProjectTeamMembersViewSet, IProjectViewSet
)

project_collection = IProjectViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

project_item = IProjectViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

project_team_member_collection = IProjectTeamMembersViewSet.as_view({
    'post': 'create',
    'delete': 'destroy_all',
    'put': 'replace_all',
})

project_team_member_item = IProjectTeamMembersViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy'
})

project_modified_since_collection = IProjectModifiedSinceViewSet.as_view({
    'get': 'list',
})

audit_item = IProjectAuditViewSet.as_view({
    'get': 'list',
})

archive_item = IProjectViewSet.as_view({
    'post': 'archive',
})

unarchive_item = IProjectViewSet.as_view({
    'post': 'unarchive',
})

project_document_collection = IProjectDocumentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

project_document_item = IProjectDocumentViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})

project_document_callback = IProjectDocumentViewSet.as_view({
    'post': 'upload_complete_callback',
})


urlpatterns = [
    path('investment', project_collection, name='investment-collection'),
    path('investment/from', project_modified_since_collection,
         name='investment-modified-since-collection'),
    path('investment/<uuid:pk>', project_item, name='investment-item'),
    path('investment/<uuid:pk>/archive', archive_item, name='archive-item'),
    path('investment/<uuid:project_pk>/team-member', project_team_member_collection,
         name='team-member-collection'),
    path('investment/<uuid:project_pk>/team-member/<uuid:adviser_pk>',
         project_team_member_item, name='team-member-item'),
    path('investment/<uuid:project_pk>/document', project_document_collection,
         name='document-collection'),
    path('investment/<uuid:project_pk>/document/<uuid:doc_pk>',
         project_document_item, name='document-item'),
    path('investment/<uuid:project_pk>/document/<uuid:doc_pk>/upload-callback',
         project_document_callback, name='document-item-callback'),
    path('investment/<uuid:pk>/unarchive', unarchive_item, name='unarchive-item'),
    path('investment/<uuid:pk>/audit', audit_item, name='audit-item'),
    path(
        'investment/',
        include(
            (proposition_urls.public_urls, 'proposition',),
            namespace='proposition'
        )
    ),
]
