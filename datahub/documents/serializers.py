from rest_framework import serializers

from datahub.documents import models


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:  # noqa: D101
        model = models.Document
        fields = '__all__'
