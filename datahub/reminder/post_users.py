# Give the post users the import-notifications and export-notifications feature flags, and a subscription for no recent interactions and new export interactions

from datahub.reminder.test.factories import (
    NewExportInteractionSubscriptionFactory,
    NoRecentExportInteractionSubscriptionFactory,
    NoRecentInvestmentInteractionSubscriptionFactory,
    UpcomingEstimatedLandDateSubscriptionFactory,
)

from datahub.reminder.models import (
    NewExportInteractionSubscription,
    NoRecentExportInteractionSubscription,
    UpcomingEstimatedLandDateSubscription,
    NoRecentInvestmentInteractionSubscription
)

from datahub.feature_flag.models import(
    UserFeatureFlagGroup
)

from datahub.company.models import(
    Advisor
)

from datahub.metadata.models import (Team, TeamRole)

advisor_ids = []
advisers = Advisor.objects.filter(id__in=advisor_ids)

export_feature_group = UserFeatureFlagGroup.objects.get(code='export-notifications')
investment_feature_group = UserFeatureFlagGroup.objects.get(code='investment-notifications')

for adviser in advisers:
    adviser.feature_groups.add(investment_feature_group)
    adviser.feature_groups.add(export_feature_group)


    #TODO - check what this subscription defaults should be
    if not NewExportInteractionSubscription.objects.filter(adviser=adviser).exists():
        NewExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[90],
            email_reminders_enabled=True,
        )
    if not NoRecentExportInteractionSubscription.objects.filter(adviser=adviser).exists():
        NoRecentExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[90],
            email_reminders_enabled=True,
        )

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

#Add 'investment-notifications' feature group to all users that are in a post team and already have 'export-notifications'
post_team_role = TeamRole.objects.filter(name="Post")[:1].get()
post_teams = Team.objects.filter(role=post_team_role).values('id')
advisors = Advisor.objects.filter(dit_team__id__in=post_teams).filter(feature_groups=investment_feature_group).exclude(feature_groups=export_feature_group)
for adviser in advisors:
    adviser.feature_groups.add(export_feature_group)
