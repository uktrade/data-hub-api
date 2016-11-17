from django.core.exceptions import ValidationError
from rest_framework import mixins
from rest_framework.decorators import detail_route
from rest_framework.exceptions import APIException
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from datahub.korben.exceptions import KorbenException


class ArchiveNoDeleteViewSet(mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.ListModelMixin,
                             GenericViewSet):
    """Implement the archive route and the read/write serializers."""

    read_serializer_class = None
    write_serializer_class = None

    @detail_route(methods=['post'])
    def archive(self, request, pk):
        """Archive the object."""
        reason = request.data.get('reason', '')
        obj = self.get_object()
        obj.archive(user=request.user, reason=reason)
        serializer = self.read_serializer_class(obj)
        return Response(data=serializer.data)

    @detail_route(methods=['get'])
    def unarchive(self, request, pk):
        """Unarchive the object."""
        obj = self.get_object()
        obj.unarchive()
        serializer = self.read_serializer_class(obj)
        return Response(data=serializer.data)

    def get_serializer_class(self):
        """Return a different serializer class for reading or writing, if defined."""
        if self.action in ('list', 'retrieve', 'archive'):
            return self.read_serializer_class
        elif self.action in ('create', 'update', 'partial_update'):
            return self.write_serializer_class

    def get_object(self):
        """Force the update from korben."""
        object = super(ArchiveNoDeleteViewSet, self).get_object()
        object = object.update_from_korben()
        return object

    def create(self, request, *args, **kwargs):
        """Override create to catch the validation errors coming from the models.

        These are not real Exceptions, rather user errors.
        """
        try:
            super().create(request, *args, **kwargs)
        except ValidationError as e:
            raise DRFValidationError(detail={'detail': e.message})

    def update(self, request, *args, **kwargs):
        """Override update to catch the validation errors coming from the models.

        These are not real Exceptions, rather user errors.
        """
        try:
            super().update(request, *args, **kwargs)
        except ValidationError as e:
            raise DRFValidationError(detail={'detail': e.message})

    def retrieve(self, request, *args, **kwargs):
        """Override to handle the exceptions coming from Korben."""
        try:
            return super().retrieve(request, *args, **kwargs)
        except KorbenException as e:
            raise APIException(detail={'detail': 'Korben error.'})
