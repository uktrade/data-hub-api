from rest_framework import serializers

from datahub.core.test.support.models import MyDisableableModel, PermissionModel


class PermissionModelSerializer(serializers.ModelSerializer):
    """Serialiser for PermissionModel."""

    class Meta:
        model = PermissionModel
        fields = '__all__'


class MyDisableableModelSerializer(serializers.ModelSerializer):
    """Serialiser for MyDisableableModel."""

    class Meta:
        model = MyDisableableModel
        fields = '__all__'
