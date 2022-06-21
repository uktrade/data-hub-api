from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datahub.investment.project.proposition.models import Proposition, PropositionStatus
from datahub.reminder.models import (
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
)
from datahub.reminder.serializers import (
    NoRecentInvestmentInteractionReminderSerializer,
    NoRecentInvestmentInteractionSubscriptionSerializer,
    UpcomingEstimatedLandDateReminderSerializer,
    UpcomingEstimatedLandDateSubscriptionSerializer,
)


class BaseSubscriptionViewset(
    viewsets.GenericViewSet,
    RetrieveModelMixin,
    UpdateModelMixin,
):
    permission_classes = ()

    def get_object(self):
        """
        Gets subscription settings instance for current user.

        If settings have not been created yet, add them.
        """
        obj, created = self.queryset.get_or_create(adviser=self.request.user)
        return obj


class NoRecentInvestmentInteractionSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = NoRecentInvestmentInteractionSubscriptionSerializer
    queryset = NoRecentInvestmentInteractionSubscription.objects.all()


class UpcomingEstimatedLandDateSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = UpcomingEstimatedLandDateSubscriptionSerializer
    queryset = UpcomingEstimatedLandDateSubscription.objects.all()


class BaseReminderViewset(viewsets.GenericViewSet, ListModelMixin):
    permission_classes = ()
    filter_backends = (OrderingFilter,)
    ordering_fields = ('created_on',)
    ordering = ('-created_on',)

    def get_queryset(self):
        return self.model_class.objects.filter(adviser=self.request.user)


class NoRecentInvestmentInteractionReminderViewset(BaseReminderViewset):
    serializer_class = NoRecentInvestmentInteractionReminderSerializer
    model_class = NoRecentInvestmentInteractionReminder


class UpcomingEstimatedLandDateReminderViewset(BaseReminderViewset):
    serializer_class = UpcomingEstimatedLandDateReminderSerializer
    model_class = UpcomingEstimatedLandDateReminder


@transaction.non_atomic_requests
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reminder_summary_view(request):
    """Returns the reminder summary."""
    estimated_land_date = UpcomingEstimatedLandDateReminder.objects.filter(
        adviser=request.user,
    ).count()
    no_recent_interaction = NoRecentInvestmentInteractionReminder.objects.filter(
        adviser=request.user,
    ).count()
    outstanding_propositions = Proposition.objects.filter(
        adviser=request.user,
        status=PropositionStatus.ONGOING,
    ).count()

    return Response({
        'estimated_land_date': estimated_land_date,
        'no_recent_investment_interaction': no_recent_interaction,
        'outstanding_propositions': outstanding_propositions,
    })
