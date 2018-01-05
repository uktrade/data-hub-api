import reversion

from datahub.investment.models import InvestmentProject

from ..base import CSVBaseCommand


class Command(CSVBaseCommand):
    """Command to update investment_project.description."""

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
        # "Id" is not a typo
        investment_project = InvestmentProject.objects.get(pk=row['Id'])
        comments = row['comments'].strip()

        if investment_project.comments != comments:
            investment_project.comments = comments

            if not simulate:
                with reversion.create_revision():
                    investment_project.save(update_fields=('comments',))
                    reversion.set_comment('Comments migration.')
