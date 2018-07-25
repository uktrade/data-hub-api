from collections import Counter
from logging import getLogger

import reversion
from django.apps import apps
from django.core.management import BaseCommand
from django.db import transaction
from reversion.models import Revision, Version

logger = getLogger(__name__)


def _get_all_model_labels():
    return [model._meta.label for model in reversion.get_registered_models()]


class Command(BaseCommand):
    """Deletes all django versions for models that no longer exist in the database."""

    def __repr__(self):
        """Python representation (used for parametrised tests)."""
        module_name = self.__class__.__module__.rsplit('.', maxsplit=1)[1]
        return f'{module_name}.{self.__class__.__name__}()'

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            '--model-label',
            action='append',
            choices=_get_all_model_labels(),
            help='Model of which we want the versions deleted. If empty, it includes all models',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """Main logic for the actual command."""
        model_labels = options['model_label'] or _get_all_model_labels()
        models = [apps.get_model(model_label) for model_label in model_labels]

        logger.info(f'Deleting versions for following deleted models: {", ".join(model_labels)}')

        counter = Counter()
        for model in models:
            _, deletions_by_model = Version.objects.get_deleted(model).delete()
            counter.update(deletions_by_model)

        # delete revisions without versions
        _, deletions_by_model = Revision.objects.filter(version__isnull=True).delete()
        counter.update(deletions_by_model)

        logger.info(f'{sum(counter.values())} records deleted. Breakdown by model:')
        for deletion_model, model_deletion_count in counter.items():
            logger.info(f'{deletion_model}: {model_deletion_count}')
