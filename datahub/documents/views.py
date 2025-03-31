"""Document views."""
from django.core.exceptions import PermissionDenied
from rest_framework import (
    filters,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response

from datahub.core.models import ArchivableModel
from datahub.core.schemas import StubSchema
from datahub.core.viewsets import (
    CoreViewSet,
    SoftDeleteCoreViewSet,
)
from datahub.documents.exceptions import TemporarilyUnavailableException
from datahub.documents.models import GenericDocument
from datahub.documents.serializers import (
    GenericDocumentCreateSerializer,
    GenericDocumentRetrieveSerializer,
    SharePointDocumentSerializer,
)
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
        """Marks document with pending_delete status and schedules an RQ job that
        performs deletion of corresponding s3 file, document and entity_document.

        Deletion of document will cascade to entity document.
        """
        instance.document.mark_deletion_pending()

        schedule_delete_document(instance.document.pk)


class GenericDocumentViewSet(SoftDeleteCoreViewSet):
    """Generic document viewset."""

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

    def get_serializer_class(self):
        """Return appropriate serializer class based on the action."""
        if self.action == 'create':
            return GenericDocumentCreateSerializer
        return GenericDocumentRetrieveSerializer

    def get_created_and_modified_by_data(self):
        """Extracts user from the request and returns a dict with created and modified by info."""
        user = self.request.user
        data = {
            'modified_by': user,
            'created_by': user,
        }
        return data

    def create(self, request, *args, **kwargs):
        """Create a GenericDocument instance along with a specific-type document instance.

        Example payload to create a SharePointDocument related to a Company:

        ```
        {
            "document_type": "documents.sharepointdocument",
            "document_data": {
                "title": "Project Proposal",
                "url": "https://sharepoint.example.com/project-proposal.docx"
            },
            "related_object_type": "company.company",
            "related_object_id": "<uuid of company>"
        }
        ```
        """
        # Validate incoming data
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        validated_data = create_serializer.validated_data

        # Get user information for created and modified by fields
        created_and_modified_by_data = self.get_created_and_modified_by_data()

        # Create specific document based on document type
        document_type = validated_data['document_type']
        document_data = validated_data['document_data']

        match f'{document_type.app_label}.{document_type.model}':
            # Unsupported document types will cause the serializer to raise a validation error.
            # Therefore, it isn't necessary to handle invalid types and return a 400 here.
            case 'documents.sharepointdocument':
                document_serializer = SharePointDocumentSerializer(data=document_data)
                document_serializer.is_valid(raise_exception=True)
                document = document_serializer.save(**created_and_modified_by_data)

        # Create GenericDocument instance
        generic_document = GenericDocument.objects.create(
            document_type=document_type,
            document_object_id=document.id,
            related_object_type=validated_data['related_object_type'],
            related_object_id=validated_data['related_object_id'],
            **created_and_modified_by_data,
        )

        # Return the created GenericDocument
        result_serializer = GenericDocumentRetrieveSerializer(generic_document)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Archive the GenericDocument and specific-type document instance."""
        generic_document = self.get_object()
        specific_type_document = generic_document.document

        # Archive specific-type document if archivable
        if issubclass(type(specific_type_document), ArchivableModel):
            specific_type_document.archive(
                request.user,
                reason='Archived instead of deleting when DELETE request received',
            )
        else:
            # TODO: consider how to call a generic delete method as this could vary between types
            raise NotImplementedError('Deletion of a non archivable model is not yet implemented.')

        # Archive generic document
        generic_document.archive(
            request.user,
            reason='Archived instead of deleting when DELETE request received',
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
