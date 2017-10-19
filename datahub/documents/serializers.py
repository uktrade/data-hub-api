from rest_framework import serializers

from datahub.documents import models


class DocumentSerializer(serializers.ModelSerializer):
    """Document Serializer.

    This serializer shouldn't be exposed to views, use it as a nested
    in other document use-specific scenarios.
    """

    class Meta:
        model = models.Document
        fields = '__all__'
