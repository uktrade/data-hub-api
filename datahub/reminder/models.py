import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from datahub.task.models import Task


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BaseSubscription(models.Model):
    """
    Base model for reminder subscriptions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    adviser = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+',
    )
    email_reminders_enabled = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return f'Subscription: {self.adviser}'


class ScheduledSubscription(models.Model):
    """
    Model for reminder adding reminder days to a subscription.
    """

    reminder_days = ArrayField(
        models.PositiveSmallIntegerField(),
        size=5,
        blank=True,
        default=list,
    )

    class Meta:
        abstract = True


class NoRecentExportInteractionSubscription(BaseSubscription, ScheduledSubscription):
    """
    Subscription to get reminders about companies with no recent interactions.
    """


class NewExportInteractionSubscription(BaseSubscription, ScheduledSubscription):
    """
    Subscription to get reminders about companies with new interactions.
    """


class NoRecentInvestmentInteractionSubscription(BaseSubscription, ScheduledSubscription):
    """
    Subscription to get reminders about projects with no recent interactions.
    """


class UpcomingEstimatedLandDateSubscription(BaseSubscription, ScheduledSubscription):
    """
    Subscription to get reminders about upcoming estimated land dates.
    """


class UpcomingTaskReminderSubscription(BaseSubscription, ScheduledSubscription):
    """
    Subscription to get reminders about upcoming tasks.
    """


class TaskAssignedToMeFromOthersSubscription(BaseSubscription):
    """
    Subscription to get reminders about upcoming tasks.
    """


class EmailDeliveryStatus(models.TextChoices):
    SENDING = ('sending', 'Sending')
    DELIVERED = ('delivered', 'Delivered')
    PERMANENT_FAILURE = ('permanent-failure', 'Permanent failure')
    TEMPORARY_FAILURE = ('temporary-failure', 'Temporary failure')
    TECHNICAL_FAILURE = ('technical-failure', 'Technical failure')

    UNKNOWN = ('unknown', 'Unknown')


class ReminderStatus(models.TextChoices):
    LIVE = ('live', 'Live')
    DISMISSED = ('dismissed', 'Dismissed')


class BaseReminderManager(models.Manager):
    """
    Base reminder manager that filters out dismissed reminders
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                models.Q(status=ReminderStatus.LIVE) | models.Q(status=''),
            )
        )


class BaseReminder(models.Model):
    """
    Base model for reminders.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    adviser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+',
    )
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=True)
    event = models.CharField(max_length=255)
    status = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        choices=ReminderStatus.choices,
        default=ReminderStatus.LIVE,
    )

    email_notification_id = models.UUIDField(null=True, blank=True)
    email_delivery_status = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        choices=EmailDeliveryStatus.choices,
        help_text='Email delivery status',
        default=EmailDeliveryStatus.UNKNOWN,
    )

    objects = BaseReminderManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.event


class NewExportInteractionReminder(BaseReminder):
    """
    New export interaction reminders.
    """

    company = models.ForeignKey(
        'company.Company',
        on_delete=models.CASCADE,
        related_name='new_export_interaction_reminders',
    )

    interaction = models.ForeignKey(
        'interaction.Interaction',
        on_delete=models.CASCADE,
        related_name='new_export_interaction_reminders',
    )

    @property
    def last_interaction_date(self):
        return self.interaction.date if self.interaction else self.company.created_on


class NoRecentExportInteractionReminder(BaseReminder):
    """
    No recent export interaction reminders.
    """

    company = models.ForeignKey(
        'company.Company',
        on_delete=models.CASCADE,
        related_name='no_recent_export_interaction_reminders',
    )

    interaction = models.ForeignKey(
        'interaction.Interaction',
        on_delete=models.CASCADE,
        related_name='no_recent_export_interaction_reminders',
        null=True,
        blank=True,
    )

    @property
    def last_interaction_date(self):
        return self.interaction.date if self.interaction else self.company.created_on


class NoRecentInvestmentInteractionReminder(BaseReminder):
    """
    No recent investment interaction reminders.
    """

    project = models.ForeignKey(
        'investment.InvestmentProject',
        on_delete=models.CASCADE,
        related_name='no_recent_investment_interaction_reminders',
    )


class UpcomingEstimatedLandDateReminder(BaseReminder):
    """
    Upcoming estimated land date reminders.
    """

    project = models.ForeignKey(
        'investment.InvestmentProject',
        on_delete=models.CASCADE,
        related_name='upcoming_estimated_land_date_reminders',
    )


class UpcomingTaskReminder(BaseReminder):
    """
    Upcoming generic task reminder.
    """

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='task',
    )


class UpcomingInvestmentProjectTaskReminder(BaseReminder):
    """
    Upcoming investment project task reminder.
    """

    investment_project_task = models.ForeignKey(
        'task.InvestmentProjectTask',
        on_delete=models.CASCADE,
        related_name='upcoming_investment_project_task_reminders',
    )


class InvestmentProjectTaskTaskAssignedToMeFromOthersReminder(BaseReminder):
    """
    Investment project task assigned to me from others notification.
    """

    investment_project_task = models.ForeignKey(
        'task.InvestmentProjectTask',
        on_delete=models.CASCADE,
        related_name='investment_project_task_task_assigned_to_me_from_others_reminder',
    )
