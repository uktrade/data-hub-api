from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid
from datahub.search.signals import disable_search_signal_receivers


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.export_potential."""

    @disable_search_signal_receivers(Company)
    def _handle(self, *args, **options):
        """
        Disables search signal receivers for companies.
        Avoid queuing huge number of Celery tasks for syncing companies to Elasticsearch.
        (Syncing can be manually performed afterwards using sync_es if required.)
        """
        return super()._handle(*args, **options)

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        score_dict = {value.lower(): key for key, value in Company.ExportPotentialScore.choices}

        pk = parse_uuid(row['datahub_company_id'])
        company = Company.objects.get(pk=pk)
        raw_potential = parse_limited_string(row['export_propensity'])
        export_potential = score_dict[raw_potential.lower()]

        if company.export_potential == export_potential:
            return

        company.export_potential = export_potential

        if simulate:
            return

        with reversion.create_revision():
            company.save(update_fields=('export_potential',))
            reversion.set_comment('Export potential updated.')
