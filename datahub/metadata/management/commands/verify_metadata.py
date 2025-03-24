import hashlib
from logging import getLogger
from operator import itemgetter

from django.apps import apps
from django.core.management.base import BaseCommand
from tabulate import tabulate

logger = getLogger(__name__)


class Command(BaseCommand):
    """Management command which returns the count for all the metadata models.
    """

    help = 'Return a count of all the metadata models.'

    def handle(self, *args, **options):
        logger.info('Gathering model counts.')

        metadata_models = list(apps.get_app_config('metadata').get_models())

        metadata_models_and_counts = [
            [model.__name__, model.objects.count()] for model in metadata_models
        ]

        sorted_models_and_counts = sorted(metadata_models_and_counts, key=itemgetter(0))

        headers = ['Model', 'Count']

        logger.info(
            f'\n{tabulate(sorted_models_and_counts, headers, tablefmt="github")}',
        )

        sorted_models_and_counts = ','.join(
            ':'.join(map(str, model_and_count))
            for model_and_count in sorted_models_and_counts
        )
        logger.info(sorted_models_and_counts)

        hash_sah256 = hashlib.sha256(
            sorted_models_and_counts.encode('utf-8'),
        ).hexdigest()

        logger.info(f'Hash value: {hash_sah256}')
