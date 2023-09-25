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
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
    UpcomingInvestmentProjectTaskReminder,
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


class UpcomingInvestmentProjectTaskReminderFactory(BaseReminderFactory):
    task = factory.SubFactory(TaskFactory)
    company = factory.SubFactory(CompanyFactory)
    project = factory.SubFactory(InvestmentProjectFactory)

    class Meta:
        model = UpcomingInvestmentProjectTaskReminder
