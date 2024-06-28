from logging import getLogger

from django.apps import apps
from django.core.management.base import BaseCommand

from tabulate import tabulate


logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Management command which returns the count for all the metadata models.
    """

    help = 'Return a count of all the metadata models.'

    def handle(self, *args, **options):
        logger.info('Gathering model counts.')

        metadata_models = list(apps.get_app_config('metadata').get_models())

        metadata_model_counts = []
        for model in metadata_models:
            metadata_model_counts.append([model.__name__, model.objects.count()])

        headers = ['Model', 'Count']

        logger.info(f'\n{tabulate(metadata_model_counts, headers, tablefmt="github")}')
