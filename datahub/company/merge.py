from collections import namedtuple
from typing import Callable, NamedTuple, Sequence, Type

from django.db import models

from datahub.company.models import (
    Company,
    CompanyExportCountry,
    CompanyExportCountryHistory,
    Contact,
)
from datahub.company_referral.models import CompanyReferral
from datahub.core.exceptions import DataHubException
from datahub.core.model_helpers import get_related_fields, get_self_referential_relations
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject
from datahub.omis.order.models import Order
from datahub.user.company_list.models import CompanyListItem, PipelineItem


# Merging is not allowed if the source company has any relations that aren't in
# this list. This is to avoid references to the source company being inadvertently
# left behind.
ALLOWED_RELATIONS_FOR_MERGING = {
    # These relations are moved to the target company on merge
    Company._meta.get_field('company_list_items').remote_field,
    Company._meta.get_field('pipeline_list_items').remote_field,
    CompanyReferral.company.field,
    Contact.company.field,
    Interaction.company.field,
    InvestmentProject.investor_company.field,
    InvestmentProject.intermediate_company.field,
    InvestmentProject.uk_company.field,
    Order.company.field,

    # Merging is allowed if the source company has export countries, but note that
    # they aren't moved to the target company (these can be manually moved in
    # the front end if required)
    CompanyExportCountry.company.field,
    CompanyExportCountryHistory.company.field,
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


def _default_object_updater(obj, field, target_company):
    setattr(obj, field, target_company)
    obj.save(update_fields=(field,))


def _company_list_item_updater(list_item, field, target_company):
    # If there is already a list item for the target company, delete this list item instead
    # as duplicates are not allowed
    if CompanyListItem.objects.filter(list_id=list_item.list_id, company=target_company).exists():
        list_item.delete()
    else:
        _default_object_updater(list_item, field, target_company)


def _pipeline_item_updater(pipeline_item, field, target_company):
    # If there is already a pipeline item for the adviser for the target company
    # delete this item instead as the same company can't be added for the same adviser again
    if PipelineItem.objects.filter(adviser=pipeline_item.adviser, company=target_company).exists():
        pipeline_item.delete()
    else:
        _default_object_updater(pipeline_item, field, target_company)


class MergeConfiguration(NamedTuple):
    """Specifies how company merging should be handled for a particular related model."""

    model: Type[models.Model]
    fields: Sequence[str]
    object_updater: Callable[[models.Model, str, Company], None] = _default_object_updater


MERGE_CONFIGURATION = [
    MergeConfiguration(Interaction, ('company',)),
    MergeConfiguration(CompanyReferral, ('company',)),
    MergeConfiguration(Contact, ('company',)),
    MergeConfiguration(InvestmentProject, INVESTMENT_PROJECT_COMPANY_FIELDS),
    MergeConfiguration(Order, ('company',)),
    MergeConfiguration(CompanyListItem, ('company',), _company_list_item_updater),
    MergeConfiguration(PipelineItem, ('company',), _pipeline_item_updater),
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

    results = {
        configuration.model: _update_objects(configuration, source_company, target_company)
        for configuration in MERGE_CONFIGURATION
    }

    source_company.mark_as_transferred(
        target_company,
        Company.TransferReason.DUPLICATE,
        user,
    )

    return results


def get_planned_changes(company: Company):
    """Gets information about the changes that would be made if merge proceeds."""
    results = {
        configuration.model: _count_objects(configuration, company)
        for configuration in MERGE_CONFIGURATION
    }

    should_archive = not company.archived

    return results, should_archive


def _update_objects(configuration: MergeConfiguration, source, target):
    """Update fields of objects from given model with the target value."""
    objects_updated = {field: 0 for field in configuration.fields}

    for field, filtered_objects in _get_objects_from_configuration(configuration, source):
        for obj in filtered_objects.iterator():
            configuration.object_updater(obj, field, target)
            objects_updated[field] += 1
    return objects_updated


def _count_objects(configuration: MergeConfiguration, company):
    """Count objects for each field from given model with the target value."""
    objects_updated = {field: 0 for field in configuration.fields}

    for field, filtered_objects in _get_objects_from_configuration(configuration, company):
        objects_updated[field] = filtered_objects.count()

    return objects_updated


def _get_objects_from_configuration(configuration: MergeConfiguration, source: Company):
    """Gets objects for each configured field."""
    for field in configuration.fields:
        yield field, configuration.model.objects.filter(**{field: source})
