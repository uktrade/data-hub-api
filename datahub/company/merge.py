from collections import namedtuple

from datahub.company.models import Company, Contact
from datahub.core.exceptions import DataHubException
from datahub.core.model_helpers import get_related_fields, get_self_referential_relations
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject
from datahub.omis.order.models import Order


ALLOWED_RELATIONS_FOR_MERGING = {
    Company._meta.get_field('company_list_items').remote_field,
    Company._meta.get_field('dnbmatchingresult').remote_field,
    Contact.company.field,
    Interaction.company.field,
    InvestmentProject.investor_company.field,
    InvestmentProject.intermediate_company.field,
    InvestmentProject.uk_company.field,
    Order.company.field,
}


INVESTMENT_PROJECT_COMPANY_FIELDS = (
    'investor_company',
    'intermediate_company',
    'uk_company',
)

FIELD_TO_DESCRIPTION_MAPPING = {
    'investor_company': ' as investor company ',
    'intermediate_company': ' as intermediate company ',
    'uk_company': ' as UK company ',
}

MergeEntrySummary = namedtuple(
    'MergeEntrySummary',
    [
        'count',
        'description',
        'model_meta',
    ],
)


MergeConfiguration = namedtuple(
    'MergeConfiguration',
    [
        'model',
        'fields',
    ],
)


MERGE_CONFIGURATION = [
    MergeConfiguration(Interaction, ('company',)),
    MergeConfiguration(Contact, ('company',)),
    MergeConfiguration(InvestmentProject, INVESTMENT_PROJECT_COMPANY_FIELDS),
    MergeConfiguration(Order, ('company',)),
]


class MergeNotAllowedError(DataHubException):
    """Merging the specified source company into the specified target company is not allowed."""


def is_company_a_valid_merge_source(company: Company):
    """Checks if company can be moved."""
    # First, check that there are no references to the company from other objects
    # (other than via the fields specified in ALLOWED_RELATIONS_FOR_MERGING).
    relations = get_related_fields(Company)

    has_related_objects = any(
        getattr(company, relation.name).count()
        for relation in relations
        if relation.remote_field not in ALLOWED_RELATIONS_FOR_MERGING
    )

    if has_related_objects:
        return False

    # Then, check that the source company itself doesn't have any references to other
    # companies.
    self_referential_fields = get_self_referential_relations(Company)
    return not any(
        getattr(company, field.name) for field in self_referential_fields
    )


def is_company_a_valid_merge_target(company: Company):
    """
    Returns whether the specified company is a valid merge target.

    This checks that the target company isn't archived.
    """
    return not company.archived


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


def merge_companies(source_company: Company, target_company: Company, user):
    """
    Merges the source company into the target company.

    MergeNotAllowedError will be raised if the merge is not allowed.
    """
    if not (
        is_company_a_valid_merge_source(source_company)
        and is_company_a_valid_merge_target(target_company)
    ):
        raise MergeNotAllowedError()

    results = _process_all_objects(
        _update_objects,
        source=source_company,
        target=target_company,
    )

    source_company.mark_as_transferred(
        target_company,
        Company.TRANSFER_REASONS.duplicate,
        user,
    )

    return results


def get_planned_changes(company: Company):
    """Gets information about the changes that would be made if merge proceeds."""
    results = _process_all_objects(
        _count_objects,
        source=company,
    )

    should_archive = not company.archived

    return results, should_archive


def _process_all_objects(process_objects_fn, **kwargs):
    """Process all objects defined in the configuration using provided function."""
    return {
        configuration.model: process_objects_fn(configuration, **kwargs)
        for configuration in MERGE_CONFIGURATION
    }


def _update_objects(configuration: MergeConfiguration, source, target):
    """Update fields of objects from given model with the target value."""
    objects_updated = {field: 0 for field in configuration.fields}

    for field, filtered_objects in _get_objects_from_configuration(configuration, source):
        for obj in filtered_objects.iterator():
            setattr(obj, field, target)
            obj.save(update_fields=(field,))
            objects_updated[field] += 1
    return objects_updated


def _count_objects(configuration: MergeConfiguration, source):
    """Count objects for each field from given model with the target value."""
    objects_updated = {field: 0 for field in configuration.fields}

    for field, filtered_objects in _get_objects_from_configuration(configuration, source):
        objects_updated[field] = filtered_objects.count()

    return objects_updated


def _get_objects_from_configuration(configuration: MergeConfiguration, source: Company):
    """Gets objects for each configured field."""
    for field in configuration.fields:
        yield field, configuration.model.objects.filter(**{field: source})
