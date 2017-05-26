"""General mixins."""
from rest_framework.decorators import detail_route
from rest_framework.response import Response


class ArchivableViewSetMixin:
    """To be used with archivable models."""

    @detail_route(methods=['post'])
    def archive(self, request, pk):
        """Archive the object."""
        reason = request.data.get('reason', '')
        obj = self.get_object()
        obj.archive(user=request.user, reason=reason)
        serializer = self.read_serializer_class(obj)
        return Response(data=serializer.data)

    @detail_route(methods=['get', 'post'])
    def unarchive(self, request, pk):
        """Unarchive the object."""
        obj = self.get_object()
        obj.unarchive()
        serializer = self.read_serializer_class(obj)
        return Response(data=serializer.data)
