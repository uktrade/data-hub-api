from django_filters.rest_framework import (
    DjangoFilterBackend,
)


from rest_framework.filters import OrderingFilter
from rest_framework.permissions import BasePermission, IsAuthenticated

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.task.models import Task
from datahub.task.serializers import TaskSerializer


class IsAdviserPermittedToEditTask(BasePermission):
    """
    Permission class to limit edit access to a task to only the original creator, or to an adviser
    that has had the task assigned to them
    """

    def has_object_permission(self, request, view, obj):
        if request.method == 'PATCH':
            return self.validate_task_permission(request, view, obj)

        if (
            request.method == 'POST'
            and request.resolver_match.view_name == 'api-v4:task:task_archive'
        ):
            return self.validate_task_permission(request, view, obj)

        return True

    def validate_task_permission(self, request, view, obj):
        if obj.created_by.id == request.user.id:
            return True
        if obj.advisers.filter(id=request.user.id).exists():
            return True
        return False


class TaskV4ViewSet(ArchivableViewSetMixin, CoreViewSet):
    """View for tasks"""

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated, IsAdviserPermittedToEditTask]
    ordering_fields = ['title']

    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.all().prefetch_related('advisers')

        archived = self.request.query_params.get('archived')
        advisers = self.request.query_params.get('advisers')

        if archived is not None:
            queryset = queryset.filter(archived=archived == 'true')
        if advisers is not None:
            queryset = queryset.filter(advisers__in=[advisers])

        return queryset
