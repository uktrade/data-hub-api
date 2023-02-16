from itertools import chain
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

    logger.info('Starting migration of ITA users')
    export_notifications_feature_group = UserFeatureFlagGroup.objects.get(
        code=EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    )
    # Get all the advisor ids that are account owner of a tier d one list company
    advisors = get_ita_users_to_migrate(export_notifications_feature_group)
    if not settings.ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS:
        logger.info(
            f'Automatic migration is disabled. The following {advisors.count()} ita users meet '
            'the criteria for migration but will not have any changes made to their accounts.',
        )
        for advisor in advisors:
            _log_ita_advisor_migration(advisor, logger)
    else:
        migrate_ita_users(export_notifications_feature_group, advisors)


def migrate_ita_users(export_notifications_feature_group, advisors):
    for advisor in advisors:
        _log_ita_advisor_migration(advisor, logger)

        export_notifications_feature_group.advisers.add(advisor.id)

        _add_advisor_to_export_subscriptions(advisor.id)

    logger.info(
        f'Migrated {advisors.count()} ita users',
    )


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
    try:
        logger.info('Starting migration of POST users')

        advisor_ids = get_post_user_ids_to_migrate()

        if not settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS:
            logger.info(
                f'Automatic migration is disabled. The following {len(advisor_ids)} post users '
                'meet the criteria for migration but will not have any changes made to their '
                'accounts.',
            )
            for advisor_id in advisor_ids:
                _log_post_advisor_migration(advisor_id, logger)
        else:
            migrate_post_users(advisor_ids)
    except Exception:
        logger.exception('Error migrating POST users')
        raise


def migrate_post_users(advisor_ids):
    export_feature_group = UserFeatureFlagGroup.objects.get(
        code=EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    )
    investment_feature_group = UserFeatureFlagGroup.objects.get(
        code=INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME,
    )

    for advisor_id in advisor_ids:
        _log_post_advisor_migration(advisor_id, logger)

        investment_feature_group.advisers.add(advisor_id)
        export_feature_group.advisers.add(advisor_id)

        _add_advisor_to_export_subscriptions(advisor_id)

        _add_advisor_to_investment_subscriptions(advisor_id)

    logger.info(
        f'Migrated {len(advisor_ids)} post users',
    )


def get_post_user_ids_to_migrate():
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

    post_advisor_ids = (
        Advisor.objects.filter(dit_team__role__id=TeamRoleID.post.value)
        .exclude(
            Q(feature_groups__code=EXPORT_NOTIFICATIONS_FEATURE_GROUP_NAME)
            & Q(feature_groups__code=INVESTMENT_NOTIFICATIONS_FEATURE_GROUP_NAME),
        )
        .values_list(
            'id',
            flat=True,
        )
    )

    def _get_advisor_ids_matching_query(query: Q):
        """Get all advisor id's matching the {query} AND are advisors with a role of POST"""
        return Advisor.objects.filter((query & Q(pk__in=post_advisor_ids))).values_list(
            'id',
            flat=True,
        )

    one_list_core_team_advisors = _get_advisor_ids_matching_query(
        Q(one_list_core_team_memberships__isnull=False)
    )

    one_list_account_owners = _get_advisor_ids_matching_query(Q(pk__in=one_list_account_owner_ids))

    project_manager_ids = _get_advisor_ids_matching_query(
        _generate_advisor_investment_project_query('investment_project_project_manager'),
    )

    project_assurance_adviser_ids = _get_advisor_ids_matching_query(
        _generate_advisor_investment_project_query('investment_project_project_assurance_adviser'),
    )

    client_relationship_manager_ids = _get_advisor_ids_matching_query(
        _generate_advisor_investment_project_query('investment_projects'),
    )

    referral_source_adviser_ids = _get_advisor_ids_matching_query(
        _generate_advisor_investment_project_query('referred_investment_projects'),
    )

    return set(
        list(
            chain(
                one_list_core_team_advisors,
                one_list_account_owners,
                project_manager_ids,
                project_assurance_adviser_ids,
                client_relationship_manager_ids,
                referral_source_adviser_ids,
            ),
        ),
    )


def _add_advisor_to_investment_subscriptions(
    advisor_id,
):
    if not NoRecentInvestmentInteractionSubscription.objects.filter(
        adviser=advisor_id,
    ).exists():
        logger.info(
            (f'Adding user {advisor_id} to NoRecentInvestmentInteractionSubscription'),
        )
        NoRecentInvestmentInteractionSubscription(
            adviser_id=advisor_id,
            reminder_days=[90],
            email_reminders_enabled=True,
        ).save()

    if not UpcomingEstimatedLandDateSubscription.objects.filter(
        adviser=advisor_id,
    ).exists():
        logger.info(
            f'Adding user {advisor_id} to UpcomingEstimatedLandDateSubscription',
        )
        UpcomingEstimatedLandDateSubscription(
            adviser_id=advisor_id,
            reminder_days=[30, 60],
            email_reminders_enabled=True,
        ).save()


def _add_advisor_to_export_subscriptions(
    advisor_id,
):
    if not NewExportInteractionSubscription.objects.filter(adviser=advisor_id).exists():
        logger.info(
            f'Adding user {advisor_id} to NewExportInteractionSubscription.',
        )
        NewExportInteractionSubscription(
            adviser_id=advisor_id,
            reminder_days=[2],
            email_reminders_enabled=True,
        ).save()

    if not NoRecentExportInteractionSubscription.objects.filter(
        adviser=advisor_id,
    ).exists():
        logger.info(
            f'Adding user {advisor_id} to NoRecentExportInteractionSubscription',
        )
        NoRecentExportInteractionSubscription(
            adviser_id=advisor_id,
            reminder_days=[90],
            email_reminders_enabled=True,
        ).save()


def _log_ita_advisor_migration(advisor, logger):

    logger.info(
        f'Migrating ITA user "{advisor.id}" to receive reminders.'
        'The feature groups this advisor is a member of are '
        f'{advisor.feature_groups.all()}. '
        'The companies this advisor is an account owner of are '
        f'{advisor.one_list_owned_companies.all()}. '
        f'The dit_team role is "{advisor.dit_team}".',
    )


def _log_post_advisor_migration(advisor_id, logger):
    logger.info(f'Migrating Post user "{advisor_id}" with to receive reminders.')


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
