from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from datahub.company.models import (
    Advisor,
    Company,
)
from datahub.core.serializers import NestedRelatedField
from datahub.documents.models import (
    GenericDocument,
    SharePointDocument,
)
from datahub.documents.utils import format_content_type


class SharePointDocumentSerializer(serializers.ModelSerializer):
    created_by = NestedRelatedField(Advisor, extra_fields=['name', 'email'], read_only=True)
    modified_by = NestedRelatedField(Advisor, extra_fields=['name', 'email'], read_only=True)

    class Meta:
        model = SharePointDocument
        fields = '__all__'


class DocumentRelatedField(serializers.RelatedField):
    """Serializer field for the GenericDocument.document field.

    Currently, only SharePointDocument objects are supported.

    To add support for another document type, add an elif statement to the to_representation
    method to check for the new model and set the serializer accordingly.

    For example:

    ```
    elif isinstance(instance, YourDocumentModel):
        serializer = YourDocumentSerializer(instance)
    ```
    """

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        if isinstance(instance, SharePointDocument):
            serializer = SharePointDocumentSerializer(instance)
        else:
            raise Exception(f'Unexpected document type: {type(instance)}')
        return serializer.data


class RelatedObjectRelatedField(serializers.RelatedField):
    """Serializer field for the GenericDocument.related_object field.

    Currently, only Company objects are support.

    To add support for another type of related object, add the model to the tuple
    in the `isinstance` call in the to_representation method - e.g.
    `isinstance(instance, (Company, YourModel, ...))`. The model must contain the fields
    `id` and `name`, otherwise, you will need to add an elif statement and customise
    the return object accordingly.
    """

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        if isinstance(instance, (Company)):
            return {
                'id': str(instance.id),
                'name': instance.name,
            }
        content_type = ContentType.objects.get_for_model(instance)
        raise Exception(f'Unexpected type of related object: {format_content_type(content_type)}')


class GenericDocumentRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for retrieving Generic Document objects."""

    created_by = NestedRelatedField(Advisor, extra_fields=['name', 'email'], read_only=True)
    modified_by = NestedRelatedField(Advisor, extra_fields=['name', 'email'], read_only=True)
    document = DocumentRelatedField(read_only=True)
    related_object = RelatedObjectRelatedField(read_only=True)

    class Meta:
        model = GenericDocument
        fields = '__all__'

    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        representation = super().to_representation(instance)
        representation.update(
            {
                'document_type': format_content_type(instance.document_type),
                'related_object_type': format_content_type(instance.related_object_type),
            },
        )
        return representation


class GenericDocumentCreateSerializer(serializers.Serializer):
    """Serializer for creating Generic Document objects.

    To add support for a new document type, add it to the list in `validate_document_type`.
    """

    # Document type information
    document_type = serializers.CharField()
    document_data = serializers.JSONField()

    # Related object information
    related_object_type = serializers.CharField()
    related_object_id = serializers.UUIDField()

    def validate_document_type(self, value):
        """Validate the document type is supported."""
        if value not in ['documents.sharepointdocument']:
            raise serializers.ValidationError(
                f"Unsupported document type: {value}. Format should be 'app_label.model'.",
            )
        app_label, model = value.split('.')
        content_type = ContentType.objects.get(app_label=app_label, model=model)
        return content_type

    def validate_related_object_type(self, value):
        """Validate the related object type exists."""
        try:
            app_label, model = value.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            return content_type
        except (ValueError, ContentType.DoesNotExist):
            raise serializers.ValidationError(
                f"Invalid related object type: {value}. Format should be 'app_label.model'.",
            )

    def validate(self, data):
        """Perform cross-field validation.

        More specifically, validate the received related_object_id exists in the
        related_object_type's queryset.
        """
        related_model = data['related_object_type'].model_class()
        try:
            related_object = related_model.objects.get(id=data['related_object_id'])
        except related_model.DoesNotExist:
            raise serializers.ValidationError(
                f'Related object with id {data["related_object_id"]} does not exist.',
            )
        data['related_object'] = related_object
        return data
