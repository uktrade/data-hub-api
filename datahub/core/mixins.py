"""General mixins."""
from django.conf import settings
from rest_framework import mixins
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from datahub.core.models import ArchivableModel
from datahub.core.schemas import StubSchema

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class ArchiveSerializer(serializers.Serializer):
    """Serializer for archive endpoints."""

    reason = serializers.CharField(max_length=MAX_LENGTH)

    def save(self, **kwargs):
        """Archives the objects."""
        self.instance.archive(user=self.context['user'], reason=self.validated_data['reason'])


class UnarchiveSerializer(serializers.Serializer):
    """Serializer for unarchive endpoints."""

    def save(self, **kwargs):
        """Restores an archived object."""
        self.instance.unarchive()


class ArchivableViewSetMixin:
    """To be used with archivable models."""

    archive_validators = []
    unarchive_validators = []

    @action(methods=['post'], detail=True, schema=StubSchema())
    def archive(self, request, pk):
        """Archive the object."""
        obj = self.get_object()
        context = {
            'user': request.user,
        }
        archive_serializer = ArchiveSerializer(
            instance=obj,
            data=request.data,
            context=context,
            validators=self.archive_validators,
        )
        archive_serializer.is_valid(raise_exception=True)
        archive_serializer.save()

        obj_serializer = self.get_serializer_class()(obj)
        return Response(data=obj_serializer.data)

    @action(methods=['post'], detail=True, schema=StubSchema())
    def unarchive(self, request, pk):
        """Unarchive the object."""
        obj = self.get_object()
        unarchive_serializer = UnarchiveSerializer(
            instance=obj,
            data=request.data,
            validators=self.unarchive_validators,
        )
        unarchive_serializer.is_valid(raise_exception=True)
        unarchive_serializer.save()

        obj_serializer = self.get_serializer_class()(obj)
        return Response(data=obj_serializer.data)


class SoftDeleteViaArchiveMixin(mixins.DestroyModelMixin):
    """To be used with models that should be archived instead of deleted"""

    def destroy(self, request, *args, **kwargs):
        """Archive instead of deleting."""
        instance = self.get_object()
        if issubclass(type(instance), ArchivableModel):
            instance.archive(
                request._user,
                reason='Archived instead of deleting when DELETE request received',
            )
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        """Override to stop the export being deleted if the instance is an archivable model"""
        if not issubclass(type(instance), ArchivableModel):
            instance.save()
