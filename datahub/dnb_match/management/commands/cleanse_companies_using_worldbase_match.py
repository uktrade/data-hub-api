from logging import getLogger

import reversion
from django.contrib.postgres.fields.jsonb import KeyTextTransform, KeyTransform
from django.core.management.base import BaseCommand
from django.db.models import Count, Exists, OuterRef, Q

from datahub.company.models import Company
from datahub.dnb_match.models import DnBMatchingResult
from datahub.dnb_match.utils import update_company_from_wb_record
from datahub.search.signals import disable_search_signal_receivers


logger = getLogger(__name__)

# list of (related field, query annotation name)
# where the 'query annotation name' can be used to access a bool value indicating
# if the company has any related field objects)
RELATED_FIELDS_MAPPING = [
    (
        'intermediate_investment_projects',
        'intermediate_investment_projects__exists',
    ),
    (
        'investee_projects',
        'investee_projects__exists',
    ),
    (
        'investor_investment_projects',
        'investor_investment_projects__exists',
    ),
    (
        'orders',
        'orders__exists',
    ),
]


def _filter_by_existing_related_objects(companies):
    """
    Can be used to check if archived companies need to be manually checked
    because some related objects exist which might need updating.

    :returns: a QuerySet with companies in the `companies` list that have any
        of the existing related objects defined in RELATED_FIELDS_MAPPING
    """
    qs = Company.objects.filter(
        id__in=[company.id for company in companies],
    )

    filters = Q()
    for field_name, annotation_name in RELATED_FIELDS_MAPPING:
        related_field = Company._meta.get_field(field_name).field

        subquery = related_field.model.objects.filter(
            **{related_field.attname: OuterRef('pk')},
        ).only('pk')

        qs = qs.annotate(
            **{annotation_name: Exists(subquery)},
        )

        filters = filters | Q(**{annotation_name: True})

    return qs.filter(filters)


class Command(BaseCommand):
    """
    Loops over all Data Hub companies with duns_number == NULL and D&B match and updates company
    fields from the matched D&B Worldbase record.
    Duplicated matches are ignored as they cannot be automatically cleansed without potential
    error.

    If the Worldbase record indicates that the company is out of business, the Data Hub
    company is archived.

    In case of errors, the failures are captured without stopping the command.

    NOTE: The command disables search signals so avoid overloading the queue.
    After it completes, you need to run `sync_es` manually to make sure
    all documents are up-to-date.
    """

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Simulates the command by performing the cleansing and rolling things back.',
        )

    def _get_companies_queryset(self):
        # subquery used to only get the matches without duplicates
        subquery_for_matched_duns_numbers = DnBMatchingResult.objects.filter(
            company__archived=False,
        ).annotate(
            dnb_match=KeyTransform('dnb_match', 'data'),
            matched_duns_number=KeyTextTransform(
                'duns_number',
                KeyTransform('dnb_match', 'data'),
            ),
        ).values(
            'matched_duns_number',
        ).annotate(
            group_count=Count('matched_duns_number'),
        ).filter(
            matched_duns_number__isnull=False,
            group_count=1,
        ).values('matched_duns_number')

        # subquery used to exclude all the duns_numbers already being used
        # (there's a unique constraint on the Company.duns_number field)
        subquery_for_existing_duns_numbers = Company.objects.filter(
            duns_number__isnull=False,
        ).values('duns_number')

        return Company.objects.annotate(
            wb_record=KeyTransform('wb_record', 'dnbmatchingresult__data'),
            matched_duns_number=KeyTextTransform(
                'DUNS Number',
                KeyTransform('wb_record', 'dnbmatchingresult__data'),
            ),
        ).filter(
            duns_number__isnull=True,
            archived=False,
            matched_duns_number__in=subquery_for_matched_duns_numbers,
        ).exclude(
            matched_duns_number__in=subquery_for_existing_duns_numbers,
        )

    @disable_search_signal_receivers(Company)
    def handle(self, *args, **options):
        """Handles the command."""
        logger.info('Started')

        result = {True: 0, False: 0}
        archived_companies = []

        for company in self._get_companies_queryset().iterator():
            succeeded_or_not, archived = self.process_company(
                company,
                simulate=options['simulate'],
            )

            result[succeeded_or_not] += 1
            if archived:
                archived_companies.append(company)

        self._print_results(result, archived_companies)

    def _process_company(self, company, simulate=False):
        """
        Updates company fields from matched Worldbase record.
        :returns: True if the company was/would have been archived
        """
        wb_record = company.dnbmatchingresult.data['wb_record']

        with reversion.create_revision():
            updated_fields = update_company_from_wb_record(
                company,
                wb_record,
                commit=not simulate,
            )

            if not simulate:
                reversion.set_comment('Updated from Dun & Bradstreet data.')

            return 'archived' in updated_fields

    def process_company(self, company, simulate=False):
        """
        Wrapper around _process_company to catch potential problems.

        :param simulate: if True, the changes will not be saved
        :returns: tuple of
            bool indicating if the company was processed successfully
            bool indicating if the company was archived
        """
        succeeded = True
        archived = False
        try:
            archived = self._process_company(company, simulate=simulate)
        except Exception as exc:
            succeeded = False
            logger.exception(f'Company {company.name} - {company.id} failed: {repr(exc)}')
        else:
            logger.info(f'Company {company.name} - OK')

        return (succeeded, archived)

    def _print_results(self, result, archived_companies):
        logger.info(
            'Finished - '
            f'succeeded: {result[True]}, '
            f'failed: {result[False]}, '
            f'archived: {len(archived_companies)}',
        )

        archived_companies_with_related_objects = _filter_by_existing_related_objects(
            archived_companies,
        )
        if len(archived_companies_with_related_objects):
            logger.info(
                'The following companies were archived but have related objects '
                'so they might require futher offline work. '
                'Please check with your Product Manager:',
            )
            for company in archived_companies_with_related_objects:
                existing_related_fields = (
                    field_name
                    for field_name, annotation_name in RELATED_FIELDS_MAPPING
                    if getattr(company, annotation_name)
                )
                logger.info(f'{company.get_absolute_url()}: {", ".join(existing_related_fields)}')
