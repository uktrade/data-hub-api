from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from datahub.company.models import (
    CompaniesHouseCompany, Company, Contact, save_to_es
)
from datahub.es.connector import ESConnector


class Command(BaseCommand):
    """ES Re-index cmd."""

    def handle(self, *args, **options):
        """Command handler."""
        esc = ESConnector()
        esc.delete_index()

        for model in (Company, CompaniesHouseCompany, Contact):
            self.re_index_model(model)

    def re_index_model(self, model):
        """Re-index model."""
        print('Re-indexing: {model}'.format(model=model.__name__))
        paginator = Paginator(model.objects.all(), 1000)
        for page_no in paginator.page_range:
            print('\rRe-indexing page {p} od {s}'.format(
                p=page_no, s=paginator.num_pages,
            ), end='')
            self.re_index_page(page_no, paginator, model)
        print()

    def re_index_page(self, page_no, paginator, model):
        """Re-index all instances from page."""
        for instance in paginator.page(page_no).object_list:
            save_to_es(model, instance)
