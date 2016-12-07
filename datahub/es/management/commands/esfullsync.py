from django.core.management import BaseCommand

from datahub.company.models import CompaniesHouseCompany, Company, Contact
from datahub.es.connector import ESConnector

MODELS_TO_SYNC = (CompaniesHouseCompany, Company, Contact)


class Command(BaseCommand):
    """Commmand class."""

    help = 'Deletes ES index and re-syncs.'

    def handle(self, *args, **options):
        """Execute the command."""
        connector = ESConnector()
        connector.delete_index()
        for model in MODELS_TO_SYNC:
            doc_type = model._meta.db_table
            self.stdout.write(self.style.HTTP_INFO('Populating {doc_type}'.format(doc_type=doc_type)))
            connector.populate(
                doc_type=doc_type,
                queryset=model.objects.all()
            )
