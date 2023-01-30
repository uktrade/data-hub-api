# Give the missing ITA users the export-notifications feature flag, and a subscription for no recent interactions and new export interactions

from datahub.reminder.test.factories import (
    NewExportInteractionSubscriptionFactory,
    NoRecentExportInteractionSubscriptionFactory,
)

from datahub.reminder.models import (
    NewExportInteractionSubscription,
    NoRecentExportInteractionSubscription,
)

from datahub.feature_flag.models import(
    UserFeatureFlagGroup
)

from datahub.company.models import(
    Advisor
)

advisor_ids = ['90d6de06-37fc-e311-8a2b-e4115bead28a','997d303a-eba0-4ae4-a2b6-55a663d2adb9','73963dc1-796c-44cb-9e6f-771b57d43fa0','cbbe4513-a6e7-e211-a78e-e4115bead28a','e12f034b-9c98-e211-a939-e4115bead28a']
advisers = Advisor.objects.filter(id__in=advisor_ids)

export_feature_group = UserFeatureFlagGroup.objects.get(code='export-notifications')

for adviser in advisers:
    adviser.feature_groups.add(export_feature_group)

    #TODO - check what this scubscript defaults should be
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
