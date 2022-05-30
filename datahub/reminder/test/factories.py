import factory

from datahub.company.test.factories import AdviserFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.reminder.models import (
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
)


class BaseSubscriptionFactory(factory.django.DjangoModelFactory):
    adviser = factory.SubFactory(AdviserFactory)


class NoRecentInvestmentInteractionSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = NoRecentInvestmentInteractionSubscription


class UpcomingEstimatedLandDateSubscriptionFactory(BaseSubscriptionFactory):
    class Meta:
        model = UpcomingEstimatedLandDateSubscription


class BaseReminderFactory(factory.django.DjangoModelFactory):
    adviser = factory.SubFactory(AdviserFactory)
    event = factory.Faker('sentence')


class NoRecentInvestmentInteractionReminderFactory(BaseReminderFactory):
    project = factory.SubFactory(InvestmentProjectFactory)

    class Meta:
        model = NoRecentInvestmentInteractionReminder


class UpcomingEstimatedLandDateReminderFactory(BaseReminderFactory):
    project = factory.SubFactory(InvestmentProjectFactory)

    class Meta:
        model = UpcomingEstimatedLandDateReminder
