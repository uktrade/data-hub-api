"""Investment project evidence document views URL config."""

from django.urls import path

from datahub.investment.evidence.views import EvidenceDocumentViewSet

evidence_document_collection = EvidenceDocumentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

evidence_document_item = EvidenceDocumentViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})

evidence_document_callback = EvidenceDocumentViewSet.as_view({
    'post': 'upload_complete_callback',
})

evidence_document_download = EvidenceDocumentViewSet.as_view({
    'get': 'download',
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
        evidence_document_callback,
        name='document-item-callback',
    ),
    path(
        'evidence-document/<uuid:entity_document_pk>/download',
        evidence_document_download,
        name='document-item-download',
    ),
]
