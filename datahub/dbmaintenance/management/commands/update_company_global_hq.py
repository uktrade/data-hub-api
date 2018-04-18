import uuid

import reversion

from datahub.company.models import Company
from ..base import CSVBaseCommand


class Command(CSVBaseCommand):
    """Command to update Company.headquarter_type."""

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--simulate',
            action='store_true',
            dest='simulate',
            default=False,
            help='If True it only simulates the command without saving the changes.',
        )

    # Assume companies with a current Global HQ are correct, as this data did not come from CDMS
    def _should_update(self, company):
        return company.global_headquarters == None

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        company = Company.objects.get(pk=row['id'])
        global_hq = None
        if _parse_uuid(row['global_hq_id']) != None:
            global_hq = Company.objects.get(pk=_parse_uuid(row['global_hq_id']))

        if self._should_update(company):
            company.global_headquarters = global_hq

            if simulate:
                return

            with reversion.create_revision():
                company.save(
                    update_fields=(
                        'global_headquarters',
                    )
                )
                reversion.set_comment('Global HQ data migration.')


def _parse_uuid(id_):
    if not id_ or id_.lower().strip() == 'null':
        return None
    return uuid.UUID(id_)
