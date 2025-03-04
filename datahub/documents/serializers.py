from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from datahub.documents.models import (
    GenericDocument,
    SharePointDocument,
)
from datahub.company.models import Company
from datahub.company.serializers import CompanySerializer
from datahub.core.serializers import NestedRelatedField

class SharePointDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = SharePointDocument
        fields = '__all__'


class DocumentRelatedField(serializers.RelatedField):
    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        if isinstance(instance, SharePointDocument):
            serializer = SharePointDocumentSerializer(instance)
        else:
            raise Exception('Unexpected document type')
        return serializer.data


class RelatedObjectRelatedField(serializers.RelatedField):
    def to_representation(self, instance):
        """Convert model instance to built-in Python (JSON friendly) data types."""
        content_type = ContentType.objects.get_for_model(instance)
        if isinstance(instance, (Company)):  # add models to tuple
            return {
                'id': instance.id,
                'name': instance.name,
                'content_type_model': content_type.model
            }
        return Exception(f'Unexpected type of related object: {content_type.model}')


class GenericDocumentSerializer(serializers.ModelSerializer):
    """Serializer for an Generic Document object."""

    document = DocumentRelatedField(read_only=True)
    related_object = RelatedObjectRelatedField(read_only=True)

    class Meta:
        model = GenericDocument
        fields = '__all__'
