from abc import ABC, abstractmethod

from django.db import transaction

from django_filters.rest_framework import (
    DjangoFilterBackend,
)


from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated


from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.task.models import InvestmentProjectTask, Task
from datahub.task.permissions import IsAdviserPermittedToEditTask
from datahub.task.serializers import (
    InvestmentProjectTaskQueryParamSerializer,
    InvestmentProjectTaskSerializer,
    TaskSerializer,
)


class TasksMixin(CoreViewSet):
    def get_tasks(self, request):
        """
        Get the task queryset that is filtered using common filters from the query params
        """
        queryset = Task.objects.all().prefetch_related('advisers')

        archived = request.query_params.get('archived')
        advisers = request.query_params.get('advisers')

        if archived is not None:
            queryset = queryset.filter(archived=archived == 'true')
        if advisers is not None:
            queryset = queryset.filter(advisers__in=[advisers])

        return queryset


class BaseTaskTypeV4ViewSet(TasksMixin, ABC):
    task_type_model_class = None

    def get_filtered_task_by_type(self, request):
        """
        Get a list of get_filtered_by_type objects filtered by the list of tasks matching
        the common filters
        """
        tasks = self.get_tasks(request)
        task_query_model_queryset = self.task_type_model_class.objects.filter(
            task__in=tasks,
        )
        return task_query_model_queryset

    def perform_create(self, serializer):
        """
        Override the default save functionality of the serializer to allow custom saving of a Task
        and associated task models
        """
        self._save_task_and_task_type_models(serializer)

    def perform_update(self, serializer):
        many_to_many_fields = ['advisers']
        # Many to many fields cannot be created automatically using the objects.create syntax.
        # They need to be added later using a set()

        extra_data = self.get_additional_data(False)

        task_data = serializer.validated_data['task']

        investment_project_task = (
            self.task_type_model_class.objects.filter(id=serializer.validated_data['id'])
            .select_related('task')
            .first()
        )

        for key, value in self._filter_task_data(task_data, many_to_many_fields).items():
            setattr(investment_project_task.task, key, value)

        advisers = task_data['advisers']
        investment_project_task.task.advisers.set(advisers)
        investment_project_task.task.save()

        task_data.update(
            {
                'id': investment_project_task.task.id,
                'created_on': investment_project_task.task.created_on,
                'modified_on': investment_project_task.task.modified_on,
            },
        )
        serializer.validated_data.update(extra_data)

    @abstractmethod
    def create_and_save_task_type_model(self, validated_data, task, extra_data):
        """
        Create a new object of type task_type_model_class and save it. This new object will assign
        the task provided
        """
        raise NotImplementedError()

    @transaction.atomic
    def _save_task_and_task_type_models(self, serializer):
        """
        Create and save both the Task model and the task_type_model_class in a single transaction.
        If either fail neither is added to django
        """
        extra_data = self.get_additional_data(True)

        task = self._create_and_save_task(serializer, extra_data)
        task_type_object = self.create_and_save_task_type_model(
            serializer.validated_data,
            task,
            extra_data,
        )

        serializer.validated_data.update(extra_data)
        serializer.validated_data.update(
            {
                'id': task_type_object.id,
                'created_on': task_type_object.created_on,
                'modified_on': task_type_object.modified_on,
            },
        )

    def _filter_task_data(self, task_data, fields_to_exclude):
        return {k: v for k, v in task_data.items() if k not in fields_to_exclude}

    def _create_and_save_task(self, serializer, extra_data):
        """
        Create a new Task object and save it
        """
        many_to_many_fields = ['advisers']
        # Many to many fields cannot be created automatically using the objects.create syntax.
        # They need to be added later using a set()

        task_data = serializer.validated_data['task']
        task_data.update(extra_data)

        advisers = task_data['advisers']

        task = Task.objects.create(
            **self._filter_task_data(task_data, many_to_many_fields),
        )
        task.advisers.set(advisers)
        task.save()
        task_data.update(
            {
                'id': task.id,
                'created_on': task.created_on,
                'modified_on': task.modified_on,
            },
        )
        return task


class TaskV4ViewSet(ArchivableViewSetMixin, TasksMixin):
    """View for tasks"""

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated, IsAdviserPermittedToEditTask]
    ordering_fields = ['title']

    serializer_class = TaskSerializer

    def get_queryset(self):
        return super().get_tasks(self.request)


class InvestmentProjectTaskV4ViewSet(BaseTaskTypeV4ViewSet):
    """
    View for InvestmentProjectTask
    """

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated, IsAdviserPermittedToEditTask]

    serializer_class = InvestmentProjectTaskSerializer

    task_type_model_class = InvestmentProjectTask

    def get_queryset(self):
        serializer = InvestmentProjectTaskQueryParamSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

        filtered_investment_projects = super().get_filtered_task_by_type(self.request)

        investment_project_id = self.request.query_params.get('investment_project')

        if investment_project_id is not None:
            filtered_investment_projects = filtered_investment_projects.filter(
                investment_project_id=investment_project_id,
            )

        return filtered_investment_projects

    def create_and_save_task_type_model(self, validated_data, task, extra_data):
        investment_project_data = validated_data['investment_project']

        investment_project_task = self.task_type_model_class.objects.create(
            task=task,
            investment_project=investment_project_data,
            **extra_data,
        )
        return investment_project_task
