from rest_framework import viewsets
from rest_framework.response import Response

from datahub.reminder.models import (
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateSubscription,
)
from datahub.reminder.serializers import (
    NoRecentInvestmentInteractionSubscriptionSerializer,
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
