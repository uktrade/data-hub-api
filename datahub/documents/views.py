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
    UploadableDocumentSerializer,
)
from datahub.documents.tasks import schedule_delete_document
from datahub.documents.utils import format_content_type


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

        To create a SharePointDocument related to a Company, POST the following payload:

        ```
        {
            'document_type': 'documents.sharepointdocument',
            'document_data': {
                'title': 'Project Proposal',
                'url': 'https://sharepoint.example.com/project-proposal.docx',
            },
            'related_object_type': 'company.company',
            'related_object_id': '<uuid of company>',
        }
        ```

        To create an UploadableDocument related to a Company, the following steps are required:

        1. POST the following payload to `documents/` to create a GenericDocument instance
        ```
        {
            'document_type': 'documents.uploadabledocument',
            'document_data': {
                'original_filename': 'project-proposal.pdf',
                'title': 'Project Proposal',
            },
            'related_object_type': 'company.company',
            'related_object_id': '<uuid of company>',
        }
        ```
        2. PUT the document contents to the signed upload url received in the response from step 1
        3. POST the same payload as step 1 to
        `documents/<uuid of generic document>/upload-complete` to signal upload has complete

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
        document_type_str = format_content_type(document_type)

        # Validate and create related document instance
        match document_type_str:
            # Unsupported document types will cause the serializer to raise a validation error.
            # Therefore, it isn't necessary to handle invalid types and return a 400 here.
            case 'documents.sharepointdocument':
                document_serializer = SharePointDocumentSerializer(data=document_data)
            case 'documents.uploadabledocument':
                document_serializer = UploadableDocumentSerializer(data=document_data)
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
        retrieve_serializer = GenericDocumentRetrieveSerializer(generic_document)
        response_data = retrieve_serializer.data

        # Include upload URL for UploadableDocument types
        if document_type_str == 'documents.uploadabledocument':
            response_data['signed_upload_url'] = document.document.get_signed_upload_url()

        return Response(response_data, status=status.HTTP_201_CREATED)

    def _get_generic_and_specific_documents(self):
        """Extracts the generic & specific document instances from the object and returns them."""
        generic_document = self.get_object()
        specific_document = generic_document.document
        return generic_document, specific_document

    def _is_uploadable_document(self):
        """Checks if current object is an uploadable document."""
        generic_document, specific_document = self._get_generic_and_specific_documents()
        if format_content_type(
            generic_document.document_type,
        ) != 'documents.uploadabledocument' or not hasattr(specific_document, 'document'):
            return False
        return True

    def _get_uploadable_document_validation_error_response(self):
        return Response(
            {'error': 'This action is only available for uploadable documents'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(methods=['post'], detail=True, schema=StubSchema())
    def upload_complete_callback(self, request, *args, **kwargs):
        """Document upload callback."""
        generic_document, specific_document = self._get_generic_and_specific_documents()

        if not self._is_uploadable_document():
            return self._get_uploadable_document_validation_error_response()

        # Schedule the virus scan for the uploadable document
        specific_document.document.schedule_av_scan()
        return Response(
            GenericDocumentRetrieveSerializer(generic_document).data,
            status=status.HTTP_200_OK,
        )

    @action(methods=['get'], detail=True, schema=StubSchema())
    def download(self, request, *args, **kwargs):
        """Provides download information."""
        generic_document, specific_document = self._get_generic_and_specific_documents()

        if not self._is_uploadable_document():
            return self._get_uploadable_document_validation_error_response()

        if not specific_document.document.scanned_on:
            raise TemporarilyUnavailableException()

        if not specific_document.document.av_clean:
            raise PermissionDenied('Document did not pass virus scanning.')

        signed_url = specific_document.document.get_signed_url()

        response = Response(GenericDocumentRetrieveSerializer(generic_document).data)
        response.data['document_url'] = signed_url
        return response

    def destroy(self, request, *args, **kwargs):
        """Archive the GenericDocument and specific-type document instance."""
        generic_document, specific_document = self._get_generic_and_specific_documents()

        # Schedule deletion of uploadable documents
        if self._is_uploadable_document():
            specific_document.document.mark_deletion_pending()
            schedule_delete_document(specific_document.document.pk)

        # Archive specific-type document if archivable
        if issubclass(type(specific_document), ArchivableModel):
            specific_document.archive(
                request.user,
                reason='Archived instead of deleting when DELETE request received',
            )

        # TODO: consider how to call a generic delete method as this could vary between types
        # TODO: handle non-uploadable and non-archivable models

        # Archive generic document
        # TODO: consider if this is appropriate when underlying uploadable document is deleted
        generic_document.archive(
            request.user,
            reason='Archived instead of deleting when DELETE request received',
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
