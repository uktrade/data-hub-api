import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.reminder.models import (
    NewExportInteractionReminder,
    NewExportInteractionSubscription,
    NoRecentExportInteractionReminder,
    NoRecentExportInteractionSubscription,
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
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
from datahub.task.test.factories import TaskFactory


class BaseSubscriptionFactory(factory.django.DjangoModelFactory):
    adviser = factory.SubFactory(AdviserFactory)


class NoRecentExportInteractionSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = NoRecentExportInteractionSubscription


class NewExportInteractionSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = NewExportInteractionSubscription


class NoRecentInvestmentInteractionSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = NoRecentInvestmentInteractionSubscription


class UpcomingEstimatedLandDateSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = UpcomingEstimatedLandDateSubscription


class UpcomingTaskReminderSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = UpcomingTaskReminderSubscription


class TaskAssignedToMeFromOthersSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = TaskAssignedToMeFromOthersSubscription


class TaskOverdueSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = TaskOverdueSubscription


class TaskCompletedSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = TaskCompletedSubscription


class TaskAmendedByOthersSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = TaskAmendedByOthersSubscription


class TaskDeletedByOthersSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = TaskDeletedByOthersSubscription


class BaseReminderFactory(factory.django.DjangoModelFactory):
    adviser = factory.SubFactory(AdviserFactory)
    event = factory.Faker('sentence')


class NewExportInteractionReminderFactory(BaseReminderFactory):
    company = factory.SubFactory(CompanyFactory)
    interaction = factory.SubFactory(CompanyInteractionFactory)

    class Meta:
        model = NewExportInteractionReminder


class NoRecentExportInteractionReminderFactory(BaseReminderFactory):
    company = factory.SubFactory(CompanyFactory)

    class Meta:
        model = NoRecentExportInteractionReminder


class NoRecentInvestmentInteractionReminderFactory(BaseReminderFactory):
    project = factory.SubFactory(InvestmentProjectFactory)

    class Meta:
        model = NoRecentInvestmentInteractionReminder


class UpcomingEstimatedLandDateReminderFactory(BaseReminderFactory):
    project = factory.SubFactory(InvestmentProjectFactory)

    class Meta:
        model = UpcomingEstimatedLandDateReminder


class UpcomingTaskReminderFactory(BaseReminderFactory):
    task = factory.SubFactory(TaskFactory)

    class Meta:
        model = UpcomingTaskReminder


class TaskAssignedToMeFromOthersReminderFactory(BaseReminderFactory):
    task = factory.SubFactory(TaskFactory)

    class Meta:
        model = TaskAssignedToMeFromOthersReminder


class TaskAmendedByOthersReminderFactory(BaseReminderFactory):
    task = factory.SubFactory(TaskFactory)

    class Meta:
        model = TaskAmendedByOthersReminder


class TaskOverdueReminderFactory(BaseReminderFactory):
    task = factory.SubFactory(TaskFactory)

    class Meta:
        model = TaskOverdueReminder


class TaskCompletedReminderFactory(BaseReminderFactory):
    task = factory.SubFactory(TaskFactory)

    class Meta:
        model = TaskCompletedReminder
