"""Generic document views URL config."""

from django.urls import path

from datahub.documents.test.my_entity_document.views import MyEntityDocumentViewSet

my_entity_document_collection = MyEntityDocumentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

my_entity_document_item = MyEntityDocumentViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})

my_entity_document_callback = MyEntityDocumentViewSet.as_view({
    'post': 'upload_complete_callback',
})

my_entity_document_download = MyEntityDocumentViewSet.as_view({
    'get': 'download',
})

urlpatterns = [
    path(
        'test-my-entity-document',
        my_entity_document_collection,
        name='test-document-collection',
    ),
    path(
        'test-my-entity-document/<uuid:entity_document_pk>',
        my_entity_document_item,
        name='test-document-item',
    ),
    path(
        'test-my-entity-document/<uuid:entity_document_pk>/upload-callback',
        my_entity_document_callback,
        name='test-document-item-callback',
    ),
    path(
        'test-my-entity-document/<uuid:entity_document_pk>/download',
        my_entity_document_download,
        name='test-document-item-download',
    ),
]
