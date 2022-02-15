from random import randrange, sample

import factory

from datahub.company.test.factories import AdviserFactory
from datahub.investment.project.notification.models import InvestmentNotificationSubscription
from datahub.investment.project.test.factories import InvestmentProjectFactory


class InvestmentNotificationSubscriptionFactory(factory.django.DjangoModelFactory):
    """Investment Notification Subscription factory."""

    investment_project = factory.SubFactory(InvestmentProjectFactory)
    adviser = factory.SubFactory(AdviserFactory)
    estimated_land_date = factory.LazyFunction(
        lambda: sample(
            InvestmentNotificationSubscription.EstimatedLandDateNotification.values,
            randrange(
                0,
                len(InvestmentNotificationSubscription.EstimatedLandDateNotification.values),
            ),
        ),
    )

    class Meta:
        model = InvestmentNotificationSubscription
