import reversion

from django.core.management.base import BaseCommand, CommandError

from datahub.company.models import Company


class Command(BaseCommand):
    help = 'Updates the export_potential field for a given Company ID'

    def add_arguments(self, parser):
        parser.add_argument('company_id', type=str, help='DataHub Company ID')
        parser.add_argument('export_propensity', type=str, help='Export Propensity Value')

    def handle(self, *args, **options):
        company_id = options['company_id']
        raw_potential = options['export_propensity']

        # Convert propensity value to match Company.ExportPotentialScore.choices
        score_dict = {value.lower(): key for key, value in Company.ExportPotentialScore.choices}
        if raw_potential.lower() not in score_dict:
            raise CommandError(f'Invalid export_propensity value: {raw_potential}')

        export_potential = score_dict[raw_potential.lower()]

        # Fetch the company by ID
        try:
            company = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            raise CommandError(f'Company with ID {company_id} does not exist')

        # Update the company if the value differs
        if company.export_potential != export_potential:
            with reversion.create_revision():
                company.export_potential = export_potential
                company.save(update_fields=('export_potential',))
                reversion.set_comment('Export potential updated via management command.')

            self.stdout.write(self.style.SUCCESS(f'Successfully updated Company ID {company_id}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'{company_id} already has the export value'))
