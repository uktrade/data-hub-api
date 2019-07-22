"""Investment project evidence document views URL config."""

from django.urls import path

from datahub.investment.project.evidence.views import EvidenceDocumentViewSet

evidence_document_collection = EvidenceDocumentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

evidence_document_item = EvidenceDocumentViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})

urlpatterns = [
    path(
        'evidence-document',
        evidence_document_collection,
        name='document-collection',
    ),
    path(
        'evidence-document/<uuid:entity_document_pk>',
        evidence_document_item,
        name='document-item',
    ),
    path(
        'evidence-document/<uuid:entity_document_pk>/upload-callback',
        EvidenceDocumentViewSet.as_action_view('upload_complete_callback'),
        name='document-item-callback',
    ),
    path(
        'evidence-document/<uuid:entity_document_pk>/download',
        EvidenceDocumentViewSet.as_action_view('download'),
        name='document-item-download',
    ),
]
