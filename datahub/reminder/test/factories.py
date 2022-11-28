import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.reminder.models import (
    NoRecentExportInteractionReminder,
    NoRecentExportInteractionSubscription,
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
)


class BaseSubscriptionFactory(factory.django.DjangoModelFactory):
    adviser = factory.SubFactory(AdviserFactory)


class NoRecentExportInteractionSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = NoRecentExportInteractionSubscription


class NoRecentInvestmentInteractionSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = NoRecentInvestmentInteractionSubscription


class UpcomingEstimatedLandDateSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = UpcomingEstimatedLandDateSubscription


class BaseReminderFactory(factory.django.DjangoModelFactory):
    adviser = factory.SubFactory(AdviserFactory)
    event = factory.Faker('sentence')


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
