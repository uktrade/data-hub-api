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
from datahub.core.constants import (
    InvestmentProjectStage,
)
from datahub.feature_flag.models import (
    UserFeatureFlagGroup,
)
from datahub.investment.project.models import InvestmentProject
from datahub.reminder import (
    EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME,
)
from datahub.reminder.models import (
    NewExportInteractionSubscription,
    NoRecentExportInteractionSubscription,
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateSubscription,
)

NOTIFICATION_SUMMARY_THRESHOLD = settings.NOTIFICATION_SUMMARY_THRESHOLD

logger = getLogger(__name__)


def run_ita_users_migration():
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
        code=EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    )
    # Get all the advisor ids that are account owner of a tier d one list company
    advisors = get_ita_users_to_migrate(export_notifications_feature_group)
    if not settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS:
        logger.info(
            'AUTOMATIC MIGRATION IS DISABLED. THE FOLLOWING %s ITA USERS MEET THE CRITERIA FOR '
            'MIGRATION BUT WILL NOT HAVE ANY CHANGES MADE TO THEIR ACCOUNTS',
            advisors.count(),
        )
        for advisor in advisors:
            _log_ita_advisor_migration(advisor, logger)
    else:
        migrate_ita_users(export_notifications_feature_group, advisors)
        logger.info(
            f'Migrated {advisors.count()} ita users',
        )


def migrate_ita_users(export_notifications_feature_group, advisors):
    for advisor in advisors:
        _log_ita_advisor_migration(advisor, logger)
        advisor.feature_groups.add(export_notifications_feature_group)

        _add_advisor_to_export_subscriptions(advisor)


def get_ita_users_to_migrate(export_notifications_feature_group):
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

    return advisors


def run_post_users_migration():
    with advisory_lock(
        'generate_post_users_advisor_list_to_assign_notifications',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Post users advisor list is already being processed by another worker.',
            )
            return

    advisors = get_post_users_to_migrate()

    if not settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS:
        logger.info(
            'AUTOMATIC MIGRATION IS DISABLED. THE FOLLOWING %s POST USERS MEET THE CRITERIA FOR '
            'MIGRATION BUT WILL NOT HAVE ANY CHANGES MADE TO THEIR ACCOUNTS',
            advisors.count(),
        )
        for advisor in advisors:
            _log_post_advisor_migration(advisor, logger)
    else:
        migrate_post_users(advisors)

        logger.info(
            f'Migrated {advisors.count()} post users',
        )


def migrate_post_users(advisors):
    export_feature_group = UserFeatureFlagGroup.objects.get(
        code=EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    )
    investment_feature_group = UserFeatureFlagGroup.objects.get(
        code=INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    )

    for advisor in advisors:
        _log_post_advisor_migration(advisor, logger)

        advisor.feature_groups.add(investment_feature_group)
        advisor.feature_groups.add(export_feature_group)

        _add_advisor_to_export_subscriptions(advisor)

        _add_advisor_to_investment_subscriptions(advisor)


def get_post_users_to_migrate():
    """Get all advisors to migrate"""
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

    advisors = (
        Advisor.objects.filter(
            (
                Q(one_list_core_team_memberships__isnull=False)
                & Q(dit_team__role__id=TeamRoleID.post.value)
            )
            | Q(pk__in=one_list_account_owner_ids)
            | (
                _generate_advisor_investment_project_query('investment_project_project_manager')
                | _generate_advisor_investment_project_query(
                    'investment_project_project_assurance_adviser',
                )
                | _generate_advisor_investment_project_query('investment_projects')
                | _generate_advisor_investment_project_query('referred_investment_projects')
            ),
        )
        .exclude(
            Q(feature_groups__code=EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME)
            & Q(feature_groups__code=INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME),
        )
        .distinct()
    )

    return advisors


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
            f'Adding user {advisor.email} to UpcomingEstimatedLandDateSubscription',
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


def _log_ita_advisor_migration(advisor, logger):

    logger.info(
        f'Migrating ITA user "{advisor.id}" with email "{advisor.email}" to receive reminders.'
        'The feature groups this advisor is a member of are '
        f'{advisor.feature_groups.all()}. '
        'The companies this advisor is an account owner of are '
        f'{advisor.one_list_owned_companies.all()}. '
        f'The dit_team role is "{advisor.dit_team}".',
    )


def _log_post_advisor_migration(advisor, logger):

    logger.info(
        f'Migrating Post user "{advisor.id}" with email "{advisor.email}" to receive reminders.'
        ' The companies this advisor is one list member of is '
        f'{advisor.one_list_core_team_memberships.all()}. '
        f'The dit_team role is "{advisor.dit_team}". '
        'The investment projects this advisor is a project manager of are '
        f'{advisor.investment_project_project_manager.all()}. '
        'The investment projects this advisor is a project assurance advisor of are '
        f'{advisor.investment_project_project_assurance_adviser.all()}. '
        'The investment projects this advisor is a client relationship manager of are '
        f'{advisor.investment_projects.all()}. '
        'The investment projects this advisor is a referral source advisor of are '
        f' {advisor.referred_investment_projects.all()}.',
    )


def _generate_advisor_investment_project_query(role):
    """
    Generate a django Q object using the advisor role to match against an investment project
    """
    return Q(
        **{
            f'{role}__isnull': False,
            f'{role}__status__in': [
                InvestmentProject.Status.ONGOING,
                InvestmentProject.Status.DELAYED,
            ],
            f'{role}__stage_id': InvestmentProjectStage.active.value.id,
        },
    )
