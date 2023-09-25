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
        queryset = (
            Task.objects.all()
            .prefetch_related('advisers')
            .select_related('task_investmentprojecttask')
        )

        archived = request.query_params.get('archived')
        advisers = request.query_params.get('advisers')

        if archived is not None:
            queryset = queryset.filter(archived=archived == 'true')
        if advisers is not None:
            queryset = queryset.filter(advisers__in=[advisers])

        return queryset


class BaseTaskTypeV4ViewSet(TasksMixin, ABC):
    task_type_model_class = None
    ordering_fields = ['task__due_date']
    # Many to many fields cannot be created automatically using the objects.create syntax.
    # They need to be added later using a set()
    many_to_many_fields = ['advisers']

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
        Override the default create functionality of the serializer to allow custom saving of a
        Task and associated task models
        """
        self._save_task_and_task_type_models(serializer)

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

    def _create_and_save_task(self, serializer, extra_data):
        """
        Create a new Task object and save it
        """

        task_data = serializer.validated_data['task']
        task_data.update(extra_data)

        task = Task.objects.create(
            **self._filter_task_data(task_data, self.many_to_many_fields),
        )

        self._save_many_to_many_task_fields(task_data, task)
        return task

    def perform_update(self, serializer):
        """
        Override the default update functionality of the serializer to allow custom saving of a
        Task and associated task models
        """
        self._update_task_and_task_type_models(serializer)

    @transaction.atomic
    def _update_task_and_task_type_models(self, serializer):
        extra_data = self.get_additional_data(False)

        task_data = serializer.validated_data['task']

        task_type_model = (
            self.task_type_model_class.objects.filter(id=self.kwargs['pk'])
            .select_related('task')
            .first()
        )

        for key, value in self._filter_task_data(task_data, self.many_to_many_fields).items():
            setattr(task_type_model.task, key, value)

        self._save_many_to_many_task_fields(task_data, task_type_model.task)

        serializer.validated_data.update(extra_data)

    def _save_many_to_many_task_fields(self, task_data, task):
        """
        Save the many to many fields on the task
        """
        advisers = task_data['advisers']
        task.advisers.set(advisers)
        task.save()
        task_data.update(
            {
                'id': task.id,
                'created_on': task.created_on,
                'modified_on': task.modified_on,
            },
        )

    @abstractmethod
    def create_and_save_task_type_model(self, validated_data, task, extra_data):
        """
        Create a new object of type task_type_model_class and save it. This new object will assign
        the task provided
        """
        raise NotImplementedError()

    def _filter_task_data(self, task_data, fields_to_exclude):
        return {k: v for k, v in task_data.items() if k not in fields_to_exclude}


class TaskV4ViewSet(ArchivableViewSetMixin, TasksMixin):
    """View for tasks"""

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated, IsAdviserPermittedToEditTask]
    ordering_fields = ['title', 'due_date']

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

        investment_project_id = serializer.validated_data.get('investment_project')

        if investment_project_id is not None:
            filtered_investment_projects = filtered_investment_projects.filter(
                investment_project_id=investment_project_id,
            )

        return filtered_investment_projects

    def create_and_save_task_type_model(self, validated_data, task, extra_data):
        investment_project_data = validated_data.get('investment_project')

        investment_project_task = self.task_type_model_class.objects.create(
            task=task,
            investment_project=investment_project_data,
            **extra_data,
        )
        return investment_project_task
