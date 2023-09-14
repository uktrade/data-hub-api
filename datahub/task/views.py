from django_filters.rest_framework import (
    DjangoFilterBackend,
)


from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from django.db import transaction

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.task.models import InvestmentProjectTask, Task
from datahub.task.permissions import IsAdviserPermittedToEditTask
from datahub.task.serializers import InvestmentProjectTaskSerializer, TaskSerializer


class BaseTaskV4ViewSet(CoreViewSet):
    def get_base_task_queryset(self, request):
        """Get the base task query that filters all task objects using common filters from the query params"""
        queryset = Task.objects.all().prefetch_related('advisers')

        archived = request.query_params.get('archived')
        advisers = request.query_params.get('advisers')

        if archived is not None:
            queryset = queryset.filter(archived=archived == 'true')
        if advisers is not None:
            queryset = queryset.filter(advisers__in=[advisers])

        return queryset


class BaseTaskTypeV4ViewSet(BaseTaskV4ViewSet):
    task_type_model_class = None

    def get_filtered_by_type(self, request):
        tasks = self.get_base_task_queryset(request)
        task_query_model_queryset = self.task_type_model_class.objects.filter(
            task__in=tasks,
        )
        return task_query_model_queryset

    def perform_create(self, serializer):
        self.save_model(serializer)

    @transaction.atomic
    def save_model(self, serializer):
        extra_data = self.get_additional_data(True)

        task = self.create_and_save_task(serializer, extra_data)
        task_type_object = self.create_and_save_task_type_model(
            serializer.validated_data, task, extra_data
        )

        serializer.validated_data.update(extra_data)
        serializer.validated_data.update(
            {
                'id': task_type_object.id,
                'created_on': task_type_object.created_on,
            }
        )

    def create_and_save_task_type_model(self, validated_data, task, extra_data):
        return None

    def create_and_save_task(self, serializer, extra_data):
        many_to_many_fields = ['advisers']
        # Many to many fields cannot be created automatically using the objects.create syntax.
        # They need to be added later using a set()

        task_data = serializer.validated_data['task']
        task_data.update(extra_data)

        advisers = task_data['advisers']

        task = Task.objects.create(
            **{k: v for k, v in task_data.items() if k not in many_to_many_fields}
        )
        task.advisers.set(advisers)
        task.save()
        task_data.update({'id': task.id, 'created_on': task.created_on})
        return task


class TaskV4ViewSet(ArchivableViewSetMixin, BaseTaskV4ViewSet):
    """View for tasks"""

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated, IsAdviserPermittedToEditTask]
    ordering_fields = ['title']

    serializer_class = TaskSerializer

    def get_queryset(self):
        return super().get_base_task_queryset(self.request)


class InvestmentProjectTaskV4ViewSet(BaseTaskTypeV4ViewSet):
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated]

    serializer_class = InvestmentProjectTaskSerializer

    task_type_model_class = InvestmentProjectTask

    def get_queryset(self):
        filtered_investment_projects = super().get_filtered_by_type(self.request)

        investment_project_id = self.request.query_params.get('investment_project')

        if investment_project_id is not None:
            filtered_investment_projects = filtered_investment_projects.filter(
                investment_project_id=investment_project_id
            )

        return filtered_investment_projects

    def create_and_save_task_type_model(self, validated_data, task, extra_data):
        investment_project_data = validated_data['investment_project']

        investment_project_task = self.task_type_model_class.objects.create(
            task=task, investment_project=investment_project_data, **extra_data
        )
        return investment_project_task
