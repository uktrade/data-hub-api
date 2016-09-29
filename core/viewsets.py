from rest_framework import mixins
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class ArchiveNoDeleteViewSet(mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.ListModelMixin,
                             GenericViewSet):
    """Implement the archive route."""

    @detail_route(methods=['post'])
    def archive(self, request, pk):
        """Archive the object."""

        reason = request.data.get('reason', '')
        obj = self.get_object()
        obj.archive(reason=reason)
        serializer = self.serializer_class(obj)
        return Response(data=serializer.data)
