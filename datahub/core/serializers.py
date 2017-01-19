from rest_framework import serializers

from datahub.core.models import TaskInfo


class ConstantModelSerializer(serializers.Serializer):
    """Constant models serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    selectable = serializers.BooleanField()

    class Meta:  # noqa: D101
        fields = '__all__'


class TaskInfoModelSerializer(serializers.ModelSerializer):
    """Task info model serializer."""

    status = serializers.CharField()

    class Meta:  # noqa: D101
        model = TaskInfo
        depth = 1
        fields = '__all__'
