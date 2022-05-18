import factory

from datahub.company.test.factories import AdviserFactory
from datahub.reminder.models import (
    NoRecentInvestmentInteractionSubscription,
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
