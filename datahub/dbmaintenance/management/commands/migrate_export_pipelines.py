from logging import getLogger

import reversion
from django.core.management.base import BaseCommand
from freezegun import freeze_time

from datahub.company.models import CompanyExport
from datahub.user.company_list.models import PipelineItem

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to migrate legacy export pipeline into a new one.

    Example of executing this command locally:
        python manage.py migrate_export_pipelines
    """

    help = 'Migrate legacy export pipelines'

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Simulate the command by querying pipeline items but without saving changes.',
        )

    def handle(self, *args, **options):
        """
        Migrates legacy pipelines
        """
        is_simulation = options['simulate']

        num_errored = 0
        num_updated = 0

        for pipeline_item in PipelineItem.objects.iterator():
            try:
                export = CompanyExport(
                    id=pipeline_item.id,
                    created_by=pipeline_item.created_by,
                    archived=pipeline_item.archived,
                    archived_on=pipeline_item.archived_on,
                    archived_reason=pipeline_item.archived_reason,
                    archived_by=pipeline_item.archived_by,
                    company=pipeline_item.company,
                    owner=pipeline_item.adviser,
                    title=pipeline_item.name,
                    sector=pipeline_item.sector,
                    estimated_export_value_amount=pipeline_item.potential_value,
                    estimated_win_date=pipeline_item.expected_win_date,
                    status=_to_export_status(pipeline_item.status),
                    export_potential=_to_export_potential(pipeline_item.likelihood_to_win),
                )
                if not is_simulation:
                    with reversion.create_revision():
                        with freeze_time(pipeline_item.created_on):
                            export.save()
                        # We need this "trick" to update modified_on field
                        # and bypass auto_now attribute
                        CompanyExport.objects.filter(id=pipeline_item.id).update(
                            modified_on=pipeline_item.modified_on,
                        )
                        export.contacts.add(*pipeline_item.contacts.all())
                        reversion.set_comment('Export pipeline migration.')

            except Exception:
                logger.exception(f'{pipeline_item} - Failed')
                num_errored += 1
            else:
                logger.info(f'{pipeline_item} - OK')
                num_updated += 1

        logger.info(f'Finished - succeeded: {num_updated}, failed: {num_errored}')


def _to_export_status(pipeline_item_status):
    mapping = {
        PipelineItem.Status.LEADS: CompanyExport.ExportStatus.INACTIVE,
        PipelineItem.Status.IN_PROGRESS: CompanyExport.ExportStatus.ACTIVE,
        PipelineItem.Status.WIN: CompanyExport.ExportStatus.WON,
    }
    return mapping[pipeline_item_status]


def _to_export_potential(pipeline_item_likelihood_to_win):
    if not pipeline_item_likelihood_to_win:
        return ''
    mapping = {
        PipelineItem.LikelihoodToWin.LOW: CompanyExport.ExportPotential.LOW,
        PipelineItem.LikelihoodToWin.MEDIUM: CompanyExport.ExportPotential.MEDIUM,
        PipelineItem.LikelihoodToWin.HIGH: CompanyExport.ExportPotential.HIGH,
    }
    return mapping[pipeline_item_likelihood_to_win]
