from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datahub.feature_flag.utils import is_user_feature_flag_group_active
from datahub.investment.project.proposition.models import Proposition, PropositionStatus
from datahub.reminder import (
    EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME,
)
from datahub.reminder.models import (
    NewExportInteractionReminder,
    NewExportInteractionSubscription,
    NoRecentExportInteractionReminder,
    NoRecentExportInteractionSubscription,
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
    ReminderStatus,
    TaskAmendedByOthersReminder,
    TaskAmendedByOthersSubscription,
    TaskAssignedToMeFromOthersReminder,
    TaskAssignedToMeFromOthersSubscription,
    TaskCompletedReminder,
    TaskCompletedSubscription,
    TaskDeletedByOthersSubscription,
    TaskOverdueReminder,
    TaskOverdueSubscription,
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
    UpcomingTaskReminder,
    UpcomingTaskReminderSubscription,
)
from datahub.reminder.serializers import (
    NewExportInteractionReminderSerializer,
    NewExportInteractionSubscriptionSerializer,
    NoRecentExportInteractionReminderSerializer,
    NoRecentExportInteractionSubscriptionSerializer,
    NoRecentInvestmentInteractionReminderSerializer,
    NoRecentInvestmentInteractionSubscriptionSerializer,
    TaskAmendedByOthersReminderSerializer,
    TaskAmendedByOthersSubscriptionSerializer,
    TaskAssignedToMeFromOthersReminderSerializer,
    TaskAssignedToMeFromOthersSubscriptionSerializer,
    TaskCompletedReminderSerializer,
    TaskCompletedSubscriptionSerializer,
    TaskDeletedByOthersSubscriptionSerializer,
    TaskOverdueReminderSerializer,
    TaskOverdueSubscriptionSerializer,
    UpcomingEstimatedLandDateReminderSerializer,
    UpcomingEstimatedLandDateSubscriptionSerializer,
    UpcomingTaskReminderSerializer,
    UpcomingTaskReminderSubscriptionSerializer,
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


class NoRecentExportInteractionSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = NoRecentExportInteractionSubscriptionSerializer
    queryset = NoRecentExportInteractionSubscription.objects.all()


class NewExportInteractionSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = NewExportInteractionSubscriptionSerializer
    queryset = NewExportInteractionSubscription.objects.all()


class NoRecentInvestmentInteractionSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = NoRecentInvestmentInteractionSubscriptionSerializer
    queryset = NoRecentInvestmentInteractionSubscription.objects.all()


class UpcomingEstimatedLandDateSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = UpcomingEstimatedLandDateSubscriptionSerializer
    queryset = UpcomingEstimatedLandDateSubscription.objects.all()


class UpcomingTaskReminderSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = UpcomingTaskReminderSubscriptionSerializer
    queryset = UpcomingTaskReminderSubscription.objects.all()


class TaskOverdueSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = TaskOverdueSubscriptionSerializer
    queryset = TaskOverdueSubscription.objects.all()


class TaskAssignedToMeFromOthersSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = TaskAssignedToMeFromOthersSubscriptionSerializer
    queryset = TaskAssignedToMeFromOthersSubscription.objects.all()


class TaskAmendedByOthersSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = TaskAmendedByOthersSubscriptionSerializer
    queryset = TaskAmendedByOthersSubscription.objects.all()


class TaskCompletedSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = TaskCompletedSubscriptionSerializer
    queryset = TaskCompletedSubscription.objects.all()


@transaction.non_atomic_requests
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reminder_subscription_summary_view(request):
    """Returns the reminder subscription summary."""

    def get_object(queryset):
        """
        Gets subscription settings instance for current user.

        If settings have not been created yet, add them.
        """
        obj, created = queryset.get_or_create(
            adviser=request.user,
        )
        return obj

    estimated_land_date = UpcomingEstimatedLandDateSubscriptionSerializer(
        get_object(UpcomingEstimatedLandDateSubscription.objects.all()),
    ).data
    no_recent_investment_interaction = NoRecentInvestmentInteractionSubscriptionSerializer(
        get_object(NoRecentInvestmentInteractionSubscription.objects.all()),
    ).data
    no_recent_export_interaction = NoRecentExportInteractionSubscriptionSerializer(
        get_object(NoRecentExportInteractionSubscription.objects.all()),
    ).data
    new_export_interaction = NewExportInteractionSubscriptionSerializer(
        get_object(NewExportInteractionSubscription.objects.all()),
    ).data
    upcoming_task_reminder = UpcomingTaskReminderSubscriptionSerializer(
        get_object(UpcomingTaskReminderSubscription.objects.all()),
    ).data
    task_assigned_to_me_from_others = TaskAssignedToMeFromOthersSubscriptionSerializer(
        get_object(TaskAssignedToMeFromOthersSubscription.objects.all()),
    ).data
    task_overdue = TaskOverdueSubscriptionSerializer(
        get_object(TaskOverdueSubscription.objects.all()),
    ).data
    task_amended_by_others = TaskAmendedByOthersSubscriptionSerializer(
        get_object(TaskAmendedByOthersSubscription.objects.all()),
    ).data
    task_completed = TaskCompletedSubscriptionSerializer(
        get_object(TaskCompletedSubscription.objects.all()),
    ).data
    task_deleted_by_others = TaskDeletedByOthersSubscriptionSerializer(
        get_object(TaskDeletedByOthersSubscription.objects.all()),
    ).data

    return Response(
        {
            'estimated_land_date': estimated_land_date,
            'no_recent_investment_interaction': no_recent_investment_interaction,
            'no_recent_export_interaction': no_recent_export_interaction,
            'new_export_interaction': new_export_interaction,
            'upcoming_task_reminder': upcoming_task_reminder,
            'task_assigned_to_me_from_others': task_assigned_to_me_from_others,
            'task_amended_by_others': task_amended_by_others,
            'task_overdue': task_overdue,
            'task_completed': task_completed,
            'task_deleted_by_others': task_deleted_by_others,
        },
    )


class BaseReminderViewset(viewsets.GenericViewSet, ListModelMixin, DestroyModelMixin):
    permission_classes = ()
    filter_backends = (OrderingFilter,)
    ordering_fields = ('created_on',)
    ordering = ('-created_on', 'pk')

    def perform_destroy(self, instance):
        """Reminder soft delete event."""
        instance.status = ReminderStatus.DISMISSED
        instance.save()

    def get_queryset(self):
        return self.model_class.objects.filter(adviser=self.request.user)


class NewExportInteractionReminderViewset(BaseReminderViewset):
    serializer_class = NewExportInteractionReminderSerializer
    model_class = NewExportInteractionReminder


class NoRecentExportInteractionReminderViewset(BaseReminderViewset):
    serializer_class = NoRecentExportInteractionReminderSerializer
    model_class = NoRecentExportInteractionReminder


class NoRecentInvestmentInteractionReminderViewset(BaseReminderViewset):
    serializer_class = NoRecentInvestmentInteractionReminderSerializer
    model_class = NoRecentInvestmentInteractionReminder


class UpcomingEstimatedLandDateReminderViewset(BaseReminderViewset):
    serializer_class = UpcomingEstimatedLandDateReminderSerializer
    model_class = UpcomingEstimatedLandDateReminder


class UpcomingTaskReminderViewset(BaseReminderViewset):
    serializer_class = UpcomingTaskReminderSerializer
    model_class = UpcomingTaskReminder


class TaskAssignedToMeFromOthersReminderViewset(BaseReminderViewset):
    serializer_class = TaskAssignedToMeFromOthersReminderSerializer
    model_class = TaskAssignedToMeFromOthersReminder


class TaskOverdueReminderViewset(BaseReminderViewset):
    serializer_class = TaskOverdueReminderSerializer
    model_class = TaskOverdueReminder


class TaskCompletedReminderViewset(BaseReminderViewset):
    serializer_class = TaskCompletedReminderSerializer
    model_class = TaskCompletedReminder


class TaskAmendedByOthersReminderViewset(BaseReminderViewset):
    serializer_class = TaskAmendedByOthersReminderSerializer
    model_class = TaskAmendedByOthersReminder


class TaskDeletedByOthersSubscriptionViewset(BaseSubscriptionViewset):
    serializer_class = TaskDeletedByOthersSubscriptionSerializer
    queryset = TaskDeletedByOthersSubscription.objects.all()


@transaction.non_atomic_requests
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reminder_summary_view(request):
    """Returns the reminder summary."""
    if is_user_feature_flag_group_active(
        INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME,
        request.user,
    ):
        estimated_land_date = UpcomingEstimatedLandDateReminder.objects.filter(
            adviser=request.user,
        ).count()
        no_recent_investment_interaction = NoRecentInvestmentInteractionReminder.objects.filter(
            adviser=request.user,
        ).count()
        outstanding_propositions = Proposition.objects.filter(
            adviser=request.user,
            status=PropositionStatus.ONGOING,
        ).count()
    else:
        estimated_land_date = 0
        no_recent_investment_interaction = 0
        outstanding_propositions = 0

    if is_user_feature_flag_group_active(
        EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
        request.user,
    ):
        no_recent_export_interaction = NoRecentExportInteractionReminder.objects.filter(
            adviser=request.user,
        ).count()
        new_export_interaction = NewExportInteractionReminder.objects.filter(
            adviser=request.user,
        ).count()
    else:
        no_recent_export_interaction = 0
        new_export_interaction = 0

    task_due_date_approaching = UpcomingTaskReminder.objects.filter(
        adviser=request.user,
    ).count()

    task_assigned_to_me_from_others = TaskAssignedToMeFromOthersReminder.objects.filter(
        adviser=request.user,
    ).count()
    task_amended_by_others = TaskAmendedByOthersReminder.objects.filter(
        adviser=request.user,
    ).count()
    task_overdue = TaskOverdueReminder.objects.filter(
        adviser=request.user,
    ).count()
    task_completed = TaskCompletedReminder.objects.filter(
        adviser=request.user,
    ).count()

    total_count = sum(
        [
            estimated_land_date,
            no_recent_investment_interaction,
            outstanding_propositions,
            no_recent_export_interaction,
            new_export_interaction,
            task_due_date_approaching,
            task_assigned_to_me_from_others,
            task_amended_by_others,
            task_overdue,
            task_completed,
        ],
    )

    return Response(
        {
            'count': total_count,
            'investment': {
                'estimated_land_date': estimated_land_date,
                'no_recent_interaction': no_recent_investment_interaction,
                'outstanding_propositions': outstanding_propositions,
            },
            'export': {
                'no_recent_interaction': no_recent_export_interaction,
                'new_interaction': new_export_interaction,
            },
            'my_tasks': {
                'due_date_approaching': task_due_date_approaching,
                'task_assigned_to_me_from_others': task_assigned_to_me_from_others,
                'task_amended_by_others': task_amended_by_others,
                'task_overdue': task_overdue,
                'task_completed': task_completed,
            },
        },
    )
