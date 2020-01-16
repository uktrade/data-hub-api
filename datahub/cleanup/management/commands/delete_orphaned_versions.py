from collections import Counter
from logging import getLogger

import reversion
from django.apps import apps
from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import CharField
from django.db.models.functions import Cast
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
            # The Version's `get_deleted` method was originally used here, but it was not working
            # quickly enough for our use case. The records to be deleted are now being determined
            # in a way that is easier on the database being used.
            _, deletions_by_model = _get_orphaned_versions_query(model).delete()
            counter.update(deletions_by_model)

        # delete revisions without versions
        _, deletions_by_model = Revision.objects.filter(version__isnull=True).delete()
        counter.update(deletions_by_model)

        logger.info(f'{sum(counter.values())} records deleted. Breakdown by model:')
        for deletion_model, model_deletion_count in counter.items():
            logger.info(f'{deletion_model}: {model_deletion_count}')


def _get_orphaned_versions_query(model):
    all_model_ids = model.objects.annotate(
        object_id=Cast('pk', CharField()),
    ).values(
        'object_id',
    )

    version_ids_to_delete = Version.objects.get_for_model(
        model,
    ).values(
        'object_id',
    ).difference(
        all_model_ids,
    )

    return Version.objects.get_for_model(model).filter(
        object_id__in=version_ids_to_delete,
    )
