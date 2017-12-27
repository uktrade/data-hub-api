from datahub.company.models import Advisor

from ..base import CSVBaseCommand


class Command(CSVBaseCommand):
    """Command to update adviser.telephone_number."""

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

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        adviser = Advisor.objects.get(pk=row['id'])
        telephone_number = row['telephone_number']

        if adviser.telephone_number != telephone_number:
            adviser.telephone_number = telephone_number

            if not simulate:
                adviser.save(update_fields=('telephone_number',))
