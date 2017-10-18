from rest_framework import serializers

from .models import MyDisableableModel


class MyDisableableModelSerializer(serializers.ModelSerializer):
    """Serialiser for MyDisableableModel."""

    class Meta:
        model = MyDisableableModel
        fields = '__all__'
