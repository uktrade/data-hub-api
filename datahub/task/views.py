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


class BaseTaskV4ViewSet():
    def get_base_queryset(self, request, type):
        queryset = Task.objects.all().prefetch_related('advisers')

        archived = request.query_params.get('archived')
        advisers = request.query_params.get('advisers')

        if archived is not None:
            queryset = queryset.filter(archived=archived == 'true')
        if advisers is not None:
            queryset = queryset.filter(advisers__in=[advisers])

        # //TODO - filter by type
        filtered_type = type.objects.filter(task__in=queryset)
        print(filtered_type)

        return queryset


class TaskV4ViewSet(ArchivableViewSetMixin, CoreViewSet, BaseTaskV4ViewSet):
    """View for tasks"""

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated, IsAdviserPermittedToEditTask]
    ordering_fields = ['title']

    serializer_class = TaskSerializer

    def get_queryset(self):
        return super().get_base_queryset(self.request)


class InvestmentProjectTaskV4ViewSet(CoreViewSet, BaseTaskV4ViewSet):
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated]

    serializer_class = InvestmentProjectTaskSerializer

    def get_queryset(self):
        query = super().get_base_queryset(self.request, InvestmentProjectTask)

        investment_project_id = self.request.query_params.get('investment_project')

        filtered_investment_projects = InvestmentProjectTask.objects.filter(
            task__in=query
        )

        if investment_project_id is not None:
            filtered_investment_projects = filtered_investment_projects.filter(
                investment_project_id=investment_project_id
            )

        return filtered_investment_projects
