from django.db import transaction
from django.db.models import Q

from django_filters.rest_framework import (
    DjangoFilterBackend,
)
from rest_framework.decorators import api_view, permission_classes

from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datahub.company.models.company import Company


from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.investment.project.models import InvestmentProject
from datahub.task.models import Task
from datahub.task.serializers import (
    TaskSerializer,
)
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.utils import record_user_event


class TasksMixin(CoreViewSet):
    def get_tasks(self, request):
        """
        Get the task queryset that is filtered using common filters from the query params
        """
        queryset = (
            Task.objects.all()
            .prefetch_related('advisers')
            .select_related(
                'investment_project',
                'company',
                'interaction',
            )
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
    filterset_fields = ['investment_project', 'company', 'interaction']

    serializer_class = TaskSerializer

    def get_queryset(self):
        return super().get_tasks(self.request)

    def perform_create(self, serializer):
        extra_data = self.get_additional_data(True)
        result = serializer.save(**extra_data)

        record_data = self.request.data
        record_data['id'] = result.id
        record_user_event(self.request, type_=UserEventType.TASK_CREATED, data=record_data)


@transaction.non_atomic_requests
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tasks_companies_and_projects(request):
    """
    Get the list of companies and projects that have tasks
    """
    user_id = request.user.id

    adviser_tasks = Task.objects.filter(
        Q(advisers__in=[user_id]) | Q(created_by=user_id),
    ).exclude(
        company__id__isnull=True,
        investment_project__id__isnull=True,
    )

    projects_queryset = (
        InvestmentProject.objects.filter(
            pk__in=adviser_tasks.values_list(
                'investment_project__id',
                flat=True,
            ),
        )
        .distinct()
        .values(
            'id',
            'name',
            'investor_company__id',
        )
        .order_by('name')
    )

    companies_queryset = (
        Company.objects.filter(
            pk__in=adviser_tasks.values_list(
                'company__id',
                flat=True,
            ),
        )
        # We dont store the company for an investment project task in the task model, as this is
        # available via the investor_company FK. We need to append any investor_company values to
        # this list
        .union(
            Company.objects.filter(
                pk__in=projects_queryset.values_list(
                    'investor_company__id',
                    flat=True,
                ),
            ),
        )
        .values('id', 'name')
        .order_by('name')
    )

    response = Response(
        {
            'companies': companies_queryset,
            'projects': projects_queryset.values(
                'id',
                'name',
            ),
        },
    )

    return response
