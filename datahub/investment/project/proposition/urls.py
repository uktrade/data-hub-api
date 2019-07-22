"""Investment project proposition views URL config."""

from django.urls import path

from datahub.investment.project.proposition.views import (
    PropositionDocumentViewSet,
    PropositionViewSet,
)

proposition_collection = PropositionViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

proposition_item = PropositionViewSet.as_view({
    'get': 'retrieve',
})

proposition_complete = PropositionViewSet.as_view({
    'post': 'complete',
})

proposition_abandon = PropositionViewSet.as_view({
    'post': 'abandon',
})

proposition_document_collection = PropositionDocumentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

proposition_document_item = PropositionDocumentViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})

proposition_document_callback = PropositionDocumentViewSet.as_action_view(
    'upload_complete_callback',
)

proposition_document_download = PropositionDocumentViewSet.as_action_view('download')

urlpatterns = [
    path('proposition', proposition_collection, name='collection'),
    path('proposition/<uuid:proposition_pk>', proposition_item, name='item'),
    path('proposition/<uuid:proposition_pk>/complete', proposition_complete, name='complete'),
    path('proposition/<uuid:proposition_pk>/abandon', proposition_abandon, name='abandon'),
    path(
        'proposition/<uuid:proposition_pk>/document',
        proposition_document_collection,
        name='document-collection',
    ),
    path(
        'proposition/<uuid:proposition_pk>/document/<uuid:entity_document_pk>',
        proposition_document_item,
        name='document-item',
    ),
    path(
        'proposition/<uuid:proposition_pk>/document/<uuid:entity_document_pk>/upload-callback',
        proposition_document_callback,
        name='document-item-callback',
    ),
    path(
        'proposition/<uuid:proposition_pk>/document/<uuid:entity_document_pk>/download',
        proposition_document_download,
        name='document-item-download',
    ),
]
