from rest_framework import viewsets
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response

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


class BaseSubscriptionViewset(viewsets.GenericViewSet):
    permission_classes = ()

    def retrieve(self, request, pk=None):
        """
        Gets subscription settings for current user.

        If settings have not been created yet, add them.
        """
        obj, created = self.queryset.get_or_create(adviser=request.user)
        serializer = self.serializer_class(obj)
        return Response(serializer.data)


class NoRecentInvestmentInteractionSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = NoRecentInvestmentInteractionSubscriptionSerializer
    queryset = NoRecentInvestmentInteractionSubscription.objects.all()


class UpcomingEstimatedLandDateSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = UpcomingEstimatedLandDateSubscriptionSerializer
    queryset = UpcomingEstimatedLandDateSubscription.objects.all()


class BaseReminderViewset(viewsets.GenericViewSet, ListModelMixin):
    permission_classes = ()

    def get_queryset(self):
        return self.model_class.objects.filter(adviser=self.request.user)


class NoRecentInvestmentInteractionReminderViewset(BaseReminderViewset):
    serializer_class = NoRecentInvestmentInteractionReminderSerializer
    model_class = NoRecentInvestmentInteractionReminder


class UpcomingEstimatedLandDateReminderViewset(BaseReminderViewset):
    serializer_class = UpcomingEstimatedLandDateReminderSerializer
    model_class = UpcomingEstimatedLandDateReminder
