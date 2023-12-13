import logging

from collections import namedtuple
from typing import Callable, NamedTuple, Sequence, Type
from typing import Union

from django.db import models

from datahub.company.models import Company, Contact
from datahub.core.exceptions import DataHubError
from datahub.core.model_helpers import get_related_fields, get_self_referential_relations

FIELD_TO_DESCRIPTION_MAPPING = {
    'companies': ' as one of participating companies',
    'investor_company': ' as investor company',
    'intermediate_company': ' as intermediate company',
    'uk_company': ' as UK company',
}

logger = logging.getLogger(__name__)

MergeEntrySummary = namedtuple(
    'MergeEntrySummary',
    [
        'count',
        'description',
        'model_meta',
    ],
)


def _default_object_updater(obj, field, target, source):
    item = getattr(obj, field)
    # if the field is m2m, replace the source with a target
    if isinstance(item, models.Manager):
        item.remove(source)
        item.add(target)
        return

    setattr(obj, field, target)
    obj.save(update_fields=(field, 'modified_on'))


class MergeConfiguration(NamedTuple):
    """Specifies how merging should be handled for a particular related model."""

    model: Type[models.Model]
    fields: Sequence[str]
    source_model: Type[models.Model]
    object_updater: Callable[[models.Model, str, models.Model], None] = _default_object_updater


class MergeNotAllowedError(DataHubError):
    """Merging the specified source into the specified target is not allowed."""


def transform_merge_results_to_merge_entry_summaries(results, skip_zeroes=False):
    """Transforms merge results into move entries to aid the presentation template."""
    merge_entries = []

    for model, fields in results.items():
        for field, num_objects_updated in fields.items():
            if num_objects_updated == 0 and skip_zeroes:
                continue

            merge_entry = MergeEntrySummary(
                num_objects_updated,
                FIELD_TO_DESCRIPTION_MAPPING.get(field, ''),
                model._meta,
            )
            merge_entries.append(merge_entry)

    return merge_entries


def get_planned_changes(model: Union[Contact, Company], merge_configuration):
    """Gets information about the changes that would be made if merge proceeds."""
    results = {
        configuration.model: _count_objects(configuration, model)
        for configuration in merge_configuration
    }

    should_archive = not model.archived

    return results, should_archive


def _count_objects(configuration: MergeConfiguration, model):
    """Count objects for each field from given model with the target value."""
    objects_updated = {field: 0 for field in configuration.fields}

    for field, filtered_objects in _get_objects_from_configuration(configuration, model):
        objects_updated[field] = filtered_objects.count()

    return objects_updated


def _get_objects_from_configuration(
    configuration: MergeConfiguration,
    source: Union[Contact, Company],
):
    """Gets objects for each configured field."""
    for field in configuration.fields:
        yield field, configuration.model.objects.filter(**{field: source})


def is_model_a_valid_merge_source(
    model: Union[Contact, Company],
    allowed_relations,
    data_structure,
):
    """Checks if model can be moved and returns fields not allowed for merging."""
    # First, check that there are no references to the model from other objects
    # (other than via the fields specified in ALLOWED_RELATIONS_FOR_MERGING).
    relations = get_related_fields(data_structure)
    disallowed_fields = []
    for relation in relations:
        if relation.remote_field not in allowed_relations:
            if getattr(model, relation.name).count():
                disallowed_fields.append(relation.name)

    if disallowed_fields:
        return False, disallowed_fields

    # Then, check that the source model itself doesn't have any references to other
    # models.
    self_referential_fields = get_self_referential_relations(data_structure)
    for field in self_referential_fields:
        if getattr(model, field.name):
            return False, [field.name]

    return True, []


def is_model_a_valid_merge_target(model: Union[Contact, Company]):
    """
    Returns whether the specified model is a valid merge target.
    This checks that the target model isn't archived.
    """
    return not model.archived


def update_objects(configuration: MergeConfiguration, source, target):
    """Update fields of objects from given model with the target value."""
    logger.info(f'Updating from {configuration.model.__name__} to source contact {source.id}.')
    objects_updated = {field: 0 for field in configuration.fields}

    for field, filtered_objects in _get_objects_from_configuration(configuration, source):
        for obj in filtered_objects.iterator():
            try:
                configuration.object_updater(obj, field, target, source)
                objects_updated[field] += 1
            except Exception as e:
                logger.exception(f'Failed {configuration.model.__name__} object {obj.pk}: {e}')
    return objects_updated
