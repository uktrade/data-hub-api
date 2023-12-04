from django_filters.rest_framework import (
    DjangoFilterBackend,
)


from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated


from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.task.models import Task
from datahub.task.serializers import (
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
            .select_related('investment_project')
            .select_related('company')
        )

        archived = request.query_params.get('archived')
        advisers = request.query_params.get('advisers')

        if archived is not None:
            queryset = queryset.filter(archived=archived == 'true')
        if advisers is not None:
            queryset = queryset.filter(advisers__in=[advisers])

        return queryset


class TaskV4ViewSet(ArchivableViewSetMixin, TasksMixin):
    """View for tasks"""

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permission_classes = [IsAuthenticated]
    ordering_fields = ['title', 'due_date', 'created_on']
    filterset_fields = ['investment_project', 'company']

    serializer_class = TaskSerializer

    def get_queryset(self):
        return super().get_tasks(self.request)
