from datahub.reminder.test.factories import (
    NoRecentInvestmentInteractionSubscriptionFactory,
    UpcomingEstimatedLandDateSubscriptionFactory,
)

advisers = Advisor.objects.filter(ids__in=[...] or whatever criteria)

feature_group = UserFeatureFlagGroup.objects.get(code='investment-notifications')

for adviser in advisers:
    adviser.feature_groups.add(feature_group)

    if not NoRecentInvestmentInteractionSubscription.objects.filter(adviser=adviser).exists():
        NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[60],
            email_reminders_enabled=True,
        )
    if not UpcomingEstimatedLandDateSubscription.objects.filter(adviser=adviser).exists():
        UpcomingEstimatedLandDateSubscriptionFactory(
           adviser=adviser,
           reminder_days=[30,60],
           email_reminders_enabled=True,
        )
