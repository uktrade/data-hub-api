from django.contrib.auth.models import User
from rest_framework import serializers


class AdvisorSerializer(serializers.ModelSerializer):
    """Advisor serializer."""

    name = serializers.CharField()

    class Meta:
        model = Advisor
        exclude = ('first_name', 'last_name')


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')
