from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from datahub.company_referral.models import CompanyReferral
from datahub.company_referral.serializers import (
    CompanyReferralSerializer,
    CompleteCompanyReferralSerializer,
)
from datahub.core.permissions import HasPermissions
from datahub.core.schemas import StubSchema
from datahub.core.viewsets import CoreViewSet


class CompanyReferralViewSet(CoreViewSet):
    """Company referral view set."""

    serializer_class = CompanyReferralSerializer
    queryset = CompanyReferral.objects.select_related(
        'company',
        'contact',
        'completed_by__dit_team',
        'created_by__dit_team',
        'interaction',
        'recipient__dit_team',
    )

    def get_queryset(self):
        """
        Get a queryset for list action that is filtered to the authenticated user's sent and
        received referrals, otherwise return original queryset.
        """
        if self.action == 'list':
            return super().get_queryset().filter(
                Q(created_by=self.request.user) | Q(recipient=self.request.user),
            )

        return super().get_queryset()

    @action(
        methods=['post'],
        detail=True,
        schema=StubSchema(),
        permission_classes=[
            HasPermissions('company_referral.change_companyreferral'),
        ],
    )
    def complete(self, request, **kwargs):
        """
        View for completing a referral.

        Completing a referral involves creating an interaction and linking the referral and
        interaction together. Hence, this view creates an interaction and updates the referral
        object accordingly.
        """
        referral = self.get_object()
        context = {
            **self.get_serializer_context(),
            # Used by HasAssociatedInvestmentProjectValidator
            'check_association_permissions': False,
            'referral': referral,
            'user': request.user,
        }
        data = {
            **request.data,
            'company': {
                'id': referral.company.pk,
            },
        }
        serializer = CompleteCompanyReferralSerializer(
            data=data,
            context=context,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
