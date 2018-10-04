from rest_framework import serializers

from datahub.documents.test.my_entity_document.models import MyEntityDocument


class MyEntityDocumentSerializer(serializers.ModelSerializer):
    """Serializer for MyEntityDocument."""

    status = serializers.SerializerMethodField()

    class Meta:
        model = MyEntityDocument
        fields = (
            'id',
            'my_field',
            'original_filename',
            'url',
            'status',
        )
        read_only_fields = ('url', 'created_by', 'created_on', 'status')

    def create(self, validated_data):
        """Create my entity document."""
        return MyEntityDocument.objects.create(
            original_filename=validated_data['original_filename'],
            my_field=validated_data['my_field'],
            created_by=self.context['request'].user,
        )

    def get_status(self, instance):
        """Get document status."""
        return instance.document.status
