from logging import getLogger

from django.conf import settings
from django.db.models import Q
from django_pglocks import advisory_lock

from datahub.company.constants import (
    OneListTierID,
    TeamRoleID,
)
from datahub.company.models import (
    Advisor,
    Company,
)
from datahub.feature_flag.models import (
    UserFeatureFlagGroup,
)
from datahub.reminder.models import (
    NewExportInteractionSubscription,
    NoRecentExportInteractionSubscription,
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateSubscription,
)

NOTIFICATION_SUMMARY_THRESHOLD = settings.NOTIFICATION_SUMMARY_THRESHOLD

logger = getLogger(__name__)


def migrate_ita_users():
    with advisory_lock(
        'generate_ita_users_advisor_list_to_assign_notifications',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'ITA users advisor list is already being processed by another worker.',
            )
            return

    export_notifications_feature_group = UserFeatureFlagGroup.objects.get(
        code='export-notifications',
    )
    # Get all the advisor ids that are account owner of a tier d one list company
    one_list_account_owner_ids = (
        Company.objects.filter(
            archived=False,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
            one_list_account_owner__id__isnull=False,
            one_list_account_owner__is_active=True,
        )
        .distinct('one_list_account_owner__id')
        .values_list(
            'one_list_account_owner__id',
            flat=True,
        )
    )
    advisors = Advisor.objects.filter(pk__in=one_list_account_owner_ids).exclude(
        feature_groups=export_notifications_feature_group,
    )

    for advisor in advisors:
        if not settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS:
            logger.info(
                'Automatic migration of users is disabled, no changes will be made to the ita'
                f' user {advisor.email} subscriptions or feature flags',
            )
        else:
            logger.info(
                f'Migrating ITA user {advisor.email} to receive reminders.',
            )
            advisor.feature_groups.add(export_notifications_feature_group)

            _add_advisor_to_export_subscriptions(advisor)

    logger.info(
        f'Migrated {advisors.count()} ita users',
    )


def migrate_post_users():
    with advisory_lock(
        'generate_post_users_advisor_list_to_assign_notifications',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Post users advisor list is already being processed by another worker.',
            )
            return

    export_feature_group = UserFeatureFlagGroup.objects.get(code='export-notifications')
    investment_feature_group = UserFeatureFlagGroup.objects.get(
        code='investment-notifications',
    )

    one_list_account_owner_ids = (
        Company.objects.filter(
            archived=False,
            one_list_tier_id=OneListTierID.tier_d_overseas_post_accounts.value,
            one_list_account_owner__id__isnull=False,
            one_list_account_owner__is_active=True,
        )
        .distinct('one_list_account_owner__id')
        .values_list(
            'one_list_account_owner__id',
            flat=True,
        )
    )

    # Get a list of all advisors (who belong to a team that has a team role of POST AND is in
    # the one list core team member table)
    # OR who are the global account manager for a company on the
    # Tier D - Overseas Post Accounts one list tier.
    # AND Exclude any who have both export-notifications and investment-notifications
    # feature flags
    advisors = (
        Advisor.objects.filter(
            (
                Q(one_list_core_team_memberships__isnull=False)
                & Q(dit_team__role__id=TeamRoleID.post.value)
            )
            | Q(pk__in=one_list_account_owner_ids),
        )
        .exclude(feature_groups__code__in=['export-notifications', 'investment-notifications'])
        .distinct()
    )

    for advisor in advisors:
        if not settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS:
            logger.info(
                'Automatic migration of users is disabled, no changes will be made to the'
                f' post user {advisor.email} subscriptions or feature flags',
            )
        else:
            logger.info(
                f'Migrating Post user {advisor.email} to receive reminders.',
            )
            advisor.feature_groups.add(investment_feature_group)
            advisor.feature_groups.add(export_feature_group)

            _add_advisor_to_export_subscriptions(advisor)

            _add_advisor_to_investment_subscriptions(advisor)

    logger.info(
        f'Migrated {advisors.count()} post users',
    )


def _add_advisor_to_investment_subscriptions(
    advisor,
):
    if not NoRecentInvestmentInteractionSubscription.objects.filter(
        adviser=advisor,
    ).exists():
        logger.info(
            (f'Adding user {advisor.email} to NoRecentInvestmentInteractionSubscription'),
        )
        NoRecentInvestmentInteractionSubscription(
            adviser=advisor,
            reminder_days=[60],
            email_reminders_enabled=True,
        ).save()
    if not UpcomingEstimatedLandDateSubscription.objects.filter(
        adviser=advisor,
    ).exists():
        logger.info(
            f'Adding  user {advisor.email} to UpcomingEstimatedLandDateSubscription',
        )
        UpcomingEstimatedLandDateSubscription(
            adviser=advisor,
            reminder_days=[30, 60],
            email_reminders_enabled=True,
        ).save()


def _add_advisor_to_export_subscriptions(
    advisor,
):
    if not NewExportInteractionSubscription.objects.filter(adviser=advisor).exists():
        logger.info(
            f'Adding user {advisor.email} to NewExportInteractionSubscription.',
        )
        NewExportInteractionSubscription(
            adviser=advisor,
            reminder_days=[90],
            email_reminders_enabled=True,
        ).save()
    if not NoRecentExportInteractionSubscription.objects.filter(
        adviser=advisor,
    ).exists():
        logger.info(
            f'Adding user {advisor.email} to NoRecentExportInteractionSubscription',
        )
        NoRecentExportInteractionSubscription(
            adviser=advisor,
            reminder_days=[90],
            email_reminders_enabled=True,
        ).save()
