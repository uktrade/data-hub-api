from rest_framework import serializers

from datahub.core.serializers import AddressSerializer
from datahub.core.test.support.models import MultiAddressModel, MyDisableableModel, PermissionModel


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


class MultiAddressModelSerializer(serializers.ModelSerializer):
    """Serialiser for MultiAddressModel."""

    primary_address = AddressSerializer(
        source_model=MultiAddressModel,
        address_source_prefix='primary_address',
    )
    secondary_address = AddressSerializer(
        source_model=MultiAddressModel,
        address_source_prefix='secondary_address',
        required=False,
        allow_null=True,
    )

    class Meta:
        model = MultiAddressModel
        fields = ['primary_address', 'secondary_address']
