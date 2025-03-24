from django.urls import path

from datahub.documents.views import GenericDocumentViewSet

generic_document_collection = GenericDocumentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})
generic_document_item = GenericDocumentViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})

urlpatterns = [
    path(
        '',
        generic_document_collection,
        name='generic-document-collection',
    ),
    path(
        '<uuid:pk>',
        generic_document_item,
        name='generic-document-item',
    ),
]
