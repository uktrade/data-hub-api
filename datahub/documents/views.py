"""Document views."""
from django.core.exceptions import PermissionDenied
from rest_framework import filters
from rest_framework.decorators import action

from datahub.core.schemas import StubSchema
from datahub.core.viewsets import (
    CoreViewSet,
    SoftDeleteCoreViewSet,
)
from datahub.documents.exceptions import TemporarilyUnavailableException
from datahub.documents.models import GenericDocument
from datahub.documents.serializers import GenericDocumentRetrieveSerializer
from datahub.documents.tasks import schedule_delete_document


class BaseEntityDocumentModelViewSet(CoreViewSet):
    """Documents ViewSet."""

    lookup_url_kwarg = 'entity_document_pk'

    def create(self, request, *args, **kwargs):
        """Create and one-time upload URL generation."""
        response = super().create(request, *args, **kwargs)
        entity_document = self.get_queryset().get(pk=response.data['id'])
        response.data['signed_upload_url'] = entity_document.document.get_signed_upload_url()

        return response

    @action(methods=['post'], detail=True, schema=StubSchema())
    def upload_complete_callback(self, request, *args, **kwargs):
        """File upload done callback."""
        entity_document = self.get_object()
        entity_document.document.schedule_av_scan()
        return self.retrieve(request)

    @action(methods=['get'], detail=True, schema=StubSchema())
    def download(self, request, *args, **kwargs):
        """Provides download information."""
        entity_document = self.get_object()

        if not entity_document.document.scanned_on:
            raise TemporarilyUnavailableException()

        if not entity_document.document.av_clean:
            raise PermissionDenied('File did not pass virus scanning.')

        url = entity_document.document.get_signed_url()

        response = super().retrieve(request)
        response.data['document_url'] = url
        return response

    def perform_destroy(self, instance):
        """
        Marks document with pending_delete status and schedules an RQ job that
        performs deletion of corresponding s3 file, document and entity_document.

        Deletion of document will cascade to entity document.
        """
        instance.document.mark_deletion_pending()

        schedule_delete_document(instance.document.pk)


class GenericDocumentViewSet(SoftDeleteCoreViewSet):
    """Generic document viewset."""

    serializer_class = GenericDocumentRetrieveSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_on']
    ordering_fields = ['created_on']

    def get_queryset(self):
        """Apply filters to queryset based on query parameters."""
        queryset = GenericDocument.objects.filter(archived=False)
        related_object_id = self.request.query_params.get('related_object_id')
        if related_object_id:
            queryset = queryset.filter(related_object_id=related_object_id)
        return queryset
