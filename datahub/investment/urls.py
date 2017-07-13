"""Investment views URL config."""

from django.conf.urls import url

from datahub.investment.views import (
    IProjectAuditViewSet, IProjectDocumentViewSet, IProjectTeamMembersViewSet,
    IProjectUnifiedViewSet
)

unified_project_collection = IProjectUnifiedViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

unified_project_item = IProjectUnifiedViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

project_team_member_collection = IProjectTeamMembersViewSet.as_view({
    'post': 'create',
    'delete': 'destroy_all'
})

project_team_member_item = IProjectTeamMembersViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy'
})

audit_item = IProjectAuditViewSet.as_view({
    'get': 'retrieve',
})

archive_item = IProjectUnifiedViewSet.as_view({
    'post': 'archive',
})

unarchive_item = IProjectUnifiedViewSet.as_view({
    'post': 'unarchive',
})

project_document_collection = IProjectDocumentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

project_document_item = IProjectDocumentViewSet.as_view({
    'get': 'retrieve',
})

project_document_callback = IProjectDocumentViewSet.as_view({
    'post': 'upload_complete_callback',
})

urlpatterns = [
    url(r'^investment$', unified_project_collection, name='investment-collection'),
    url(r'^investment/(?P<pk>[0-9a-z-]{36})$', unified_project_item,
        name='investment-item'),
    url(r'^investment/(?P<pk>[0-9a-z-]{36})/archive$', archive_item,
        name='archive-item'),
    url(r'^investment/(?P<project_pk>[0-9a-z-]{36})/team-member$', project_team_member_collection,
        name='team-member-collection'),
    url(r'^investment/(?P<project_pk>[0-9a-z-]{36})/team-member/(?P<adviser_pk>[0-9a-z-]{36})$',
        project_team_member_item, name='team-member-item'),
    url(r'^investment/(?P<project_pk>[0-9a-z-]{36})/document$', project_document_collection,
        name='document-collection'),
    url(r'^investment/(?P<project_pk>[0-9a-z-]{36})/document/(?P<doc_pk>[0-9a-z-]{36})$',
        project_document_item, name='document-item'),
    url(r'^investment/(?P<project_pk>[0-9a-z-]{36})/document/(?P<doc_pk>[0-9a-z-]{36})/upload-callback$',
        project_document_callback, name='document-item-callback'),
    url(r'^investment/(?P<pk>[0-9a-z-]{36})/unarchive$', unarchive_item,
        name='unarchive-item'),
    url(r'^investment/(?P<pk>[0-9a-z-]{36})/audit$', audit_item,
        name='audit-item'),
]
