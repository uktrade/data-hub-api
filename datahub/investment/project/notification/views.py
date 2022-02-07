from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datahub.investment.project.notification.models import InvestmentNotificationSubscription
from datahub.investment.project.notification.serializers import (
    InvestmentNotificationSubscriptionSerializer,
)


def get_notification_subscription(request, project_pk):
    """
    Get investment project notification subscription details.

    If subscription does not exist, return default empty object.
    """
    subscription = InvestmentNotificationSubscription.objects.filter(
        investment_project_id=project_pk,
        adviser_id=request.user.id,
    ).first()

    if not subscription:
        serializer = InvestmentNotificationSubscriptionSerializer(data={
            'estimated_land_date': [],
        })
        serializer.is_valid(raise_exception=True)
    else:
        serializer = InvestmentNotificationSubscriptionSerializer(subscription)

    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def get_or_update_notification_subscription(request, project_pk):
    """
    Update investment project notification subscription details.

    If subscription does not exist, create an empty record
    """
    is_post = request.method == 'POST'

    if not is_post:
        return get_notification_subscription(request, project_pk)

    subscription = InvestmentNotificationSubscription.objects.filter(
        investment_project_id=project_pk,
        adviser_id=request.user.id,
    ).first()

    if not subscription:
        subscription = InvestmentNotificationSubscription.objects.create(
            investment_project_id=project_pk,
            adviser_id=request.user.id,
            estimated_land_date=[],
        )

    serializer = InvestmentNotificationSubscriptionSerializer(
        instance=subscription,
        data=request.data,
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)
