from rest_framework import serializers

from .models import MyDisableableModel


class MyDisableableModelSerializer(serializers.ModelSerializer):
    """Serialiser for MyDisableableModel."""

    class Meta:  # noqa: D101
        model = MyDisableableModel
        fields = '__all__'
