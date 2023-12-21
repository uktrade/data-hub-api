from django.db import transaction
from django.db.models import F, Q

from django_filters.rest_framework import (
    DjangoFilterBackend,
)
from rest_framework.decorators import api_view, permission_classes

from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


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


@transaction.non_atomic_requests
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tasks_companies_and_projects(request):
    """
    Get the list of companies and projects that have tasks
    """
    user_id = request.user.id
    queryset = (
        Task.objects.filter(Q(advisers__in=[user_id]) | Q(created_by=user_id))
        .select_related('investment_project')
        .select_related('company')
    )

    companies = (
        queryset
        .values('company__name', 'company__id')
        .annotate(company_name=F('company__name'), company_id=F('company__id'))
        .values('company_name', 'company_id')
        .exclude(company_name__isnull=True)
        .distinct()
    )

    projects = (
        queryset
        .values('investment_project__name', 'investment_project__id')
        .annotate(
            project_name=F('investment_project__name'),
            project_id=F('investment_project__id'),
        )
        .values('project_name', 'project_id')
        .exclude(project_name__isnull=True)
        .distinct()
    )

    response = Response(
        {
            'companies': companies,
            'projects': projects,
        },
    )

    return response
