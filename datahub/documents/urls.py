from django.conf.urls import url

from datahub.documents.views import IProjectDocumentViewSet


document_collection = IProjectDocumentViewSet.as_view({
    'get': 'list',
})

document_item = IProjectDocumentViewSet.as_view({
    'get': 'retrieve',
})


urlpatterns = [
    url(r'^documents$', document_collection, name='document'),
    url(r'^documents/(?P<pk>[0-9a-z-]{36})$', document_item,
        name='document-item'),
]
