from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope

from datahub.company.models import Company, CompanyPermission
from datahub.company.timeline.client import DataScienceCompanyAPIClient
from datahub.company.timeline.exceptions import InvalidCompanyNumberError
from datahub.company.timeline.serializers import TimelineEventSerializer
from datahub.core.permissions import HasPermissions
from datahub.core.viewsets import CoreViewSet
from datahub.oauth.scopes import Scope


class CompanyTimelineViewSet(CoreViewSet):
    """Company timeline views."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
            f'company.{CompanyPermission.view_company_timeline}',
        ),
    )
    queryset = Company.objects.all()
    serializer_class = TimelineEventSerializer

    def list(self, request, *args, **kwargs):
        """Lists timeline events (paginated)."""
        company = self.get_object()
        events = _get_events_for_company(company)
        page = self.paginator.paginate_queryset(events, self.request)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


def _get_events_for_company(company):
    client = DataScienceCompanyAPIClient()
    try:
        return client.get_timeline_events_by_company_number(company.company_number)
    except InvalidCompanyNumberError:
        return []
