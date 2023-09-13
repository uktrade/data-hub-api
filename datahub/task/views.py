from django_filters.rest_framework import (
    DjangoFilterBackend,
)


from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.task.models import InvestmentProjectTask, Task
from datahub.task.permissions import IsAdviserPermittedToEditTask
from datahub.task.serializers import InvestmentProjectTaskSerializer, TaskSerializer


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


class InvestmentProjectTaskV4ViewSet(ArchivableViewSetMixin, CoreViewSet):
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated]

    serializer_class = InvestmentProjectTaskSerializer

    queryset = InvestmentProjectTask.objects.all()
