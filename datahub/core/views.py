from rest_framework import mixins
from rest_framework import viewsets

from .models import TaskInfo
from .serializers import TaskInfoModelSerializer


class TaskInfoReadOnlyViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    """Task info read only viewset."""

    serializer_class = TaskInfoModelSerializer
    queryset = TaskInfo.objects.select_related('user')
