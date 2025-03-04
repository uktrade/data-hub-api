from django.urls import path

from datahub.documents.views import GenericDocumentViewSet


generic_document_collection = GenericDocumentViewSet.as_view({
    'get': 'list',
})

urlpatterns = [
    path(
        '',
        generic_document_collection,
        name='generic-document-collection',
    ),
]
