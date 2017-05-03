from rest_framework import serializers


class ConstantModelSerializer(serializers.Serializer):
    """Constant models serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    selectable = serializers.BooleanField()

    class Meta:  # noqa: D101
        fields = '__all__'
