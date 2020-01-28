from logging import getLogger

from django.core.management.base import BaseCommand
from django.db.models import Q

from datahub.company.models import Company

logger = getLogger(__name__)

# TODO: Remove this query command when we are done with it.
# Side note: commands of this format will only be necessary until we have a
# readonly replica DB to perform safe queries against.


def _get_company_ids(one_list_tier_ids, account_manager_ids):
    """
    Get an iterable of duns-linked company ids that match the one list tier and account manager
    arguments. Matching companies will be determined by those that meet these filters
    themselves, or those whose global headquarters do.
    """
    tier_matches = Q(one_list_tier_id__in=one_list_tier_ids)
    headquarter_tier_matches = Q(global_headquarters__one_list_tier_id__in=one_list_tier_ids)

    companies = Company.objects.filter(
        duns_number__isnull=False,
        archived=False,
    ).filter(tier_matches | headquarter_tier_matches)

    if account_manager_ids:
        account_owner_matches = Q(one_list_account_owner_id__in=account_manager_ids)
        headquarter_account_owner_matches = Q(
            global_headquarters__one_list_account_owner_id__in=account_manager_ids,
        )
        companies = companies.filter(
            account_owner_matches | headquarter_account_owner_matches,
        )

    return companies.values_list('id', flat=True)


class Command(BaseCommand):
    """
    Command to query for the ids of duns-linked companies for a particular set of
    one list tiers and (optionally) particular set of account managers.
    """

    def add_arguments(self, parser):
        """
        Set arguments for the management command.
        """
        parser.add_argument(
            '--one-list-tier-ids',
            nargs='+',
            help='The IDs of the one list tiers to filter by.',
            required=True,
        )
        parser.add_argument(
            '--account-manager-ids',
            nargs='+',
            help='The IDs of the account managers to filter by.',
            required=False,
        )

    def handle(self, *args, **options):
        """
        Run the query and output the results as an info message to the log file.
        """
        one_list_tier_ids = options['one_list_tier_ids']
        account_manager_ids = options.get('account_manager_ids') or []
        ids = _get_company_ids(one_list_tier_ids, account_manager_ids)

        all_ids_str = '\n'.join(str(company_id) for company_id in ids)
        logger.info(all_ids_str)
