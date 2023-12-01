from collections import namedtuple
from typing import Callable, NamedTuple, Sequence, Type

from django.db import models

from datahub.company_referral.models import CompanyReferral
from datahub.company.models import Company, Contact, CompanyExport
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject
from datahub.omis.order.models import Order, Quote
from datahub.user.company_list.models import CompanyListItem, PipelineItem
from datahub.core.model_helpers import get_related_fields, get_self_referential_relations

ALLOWED_RELATIONS_FOR_MERGING = {
    # These relations are moved to the target company on merge
    Company._meta.get_field('pipeline_list_items').remote_field,
    CompanyReferral.contact.field,
    Interaction.contacts.field,
    InvestmentProject.client_contacts.field,
    Order.contact.field,
    Quote.accepted_by.field,
    CompanyExport.contacts.field,
}

MergeEntrySummary = namedtuple(
    'MergeEntrySummary',
    [
        'count',
        'description',
        'model_meta',
    ],
)


def _default_object_updater(obj, field, target_contact, source_contact):
    item = getattr(obj, field)
    # if the field is m2m, replace the source contact with a target contact
    if isinstance(item, models.Manager):
        item.remove(source_contact)
        item.add(target_contact)
        return

    setattr(obj, field, target_contact)
    obj.save(update_fields=(field, 'modified_on'))

def _contact_list_item_updater(list_item, field, target_contact, source_contact):
    # If there is already a list item for the target contact, delete this list item instead
    # as duplicates are not allowed
    if CompanyListItem.objects.filter(list_id=list_item.list_id, contact=target_contact).exists():
        list_item.delete()
    else:
        _default_object_updater(list_item, field, target_contact, source_contact)

def _pipeline_item_updater(pipeline_item, field, target_contact, source_contact):
    # If there is already a pipeline item for the adviser for the target contact
    # delete this item instead as the same contact can't be added for the same adviser again
    if PipelineItem.objects.filter(adviser=pipeline_item.adviser, contact=target_contact).exists():
        pipeline_item.delete()
    else:
        _default_object_updater(pipeline_item, field, target_contact, source_contact)

class MergeConfiguration(NamedTuple):
    """Specifies how contct merging should be handled for a particular related model."""

    model: Type[models.Model]
    fields: Sequence[str]
    object_updater: Callable[[models.Model, str, Contact], None] = _default_object_updater

MERGE_CONFIGURATION = [
    MergeConfiguration(Interaction, ('contacts',)),
    MergeConfiguration(CompanyReferral, ('contact',)),
    MergeConfiguration(InvestmentProject, ('client_contacts',) ),
    MergeConfiguration(Order, ('contact',)),
    MergeConfiguration(Quote, ('accepted_by',)),
    MergeConfiguration(CompanyExport, ('contacts',)),
    # MergeConfiguration(CompanyListItem, ('contacts',), _contact_list_item_updater),
    MergeConfiguration(PipelineItem, ('contacts',), _pipeline_item_updater),

]

def transform_merge_results_to_merge_entry_summaries(results, skip_zeroes=False):
    """Transforms merge results into move entries to aid the presentation template."""
    merge_entries = []

    for model, fields in results.items():
        for field, num_objects_updated in fields.items():
            if num_objects_updated == 0 and skip_zeroes:
                continue

            merge_entry = MergeEntrySummary(
                num_objects_updated,
                "This is a contact",
                # FIELD_TO_DESCRIPTION_MAPPING.get(field, ''),
                model._meta,
            )
            merge_entries.append(merge_entry)

    return merge_entries

def get_planned_changes(contact: Contact):
    print("/////////////")
    """Gets information about the changes that would be made if merge proceeds."""
    results = {
        configuration.model: _count_objects(configuration, contact)
        for configuration in MERGE_CONFIGURATION
    }
    print(results)

    should_archive = not contact.archived

    return results, should_archive

def _count_objects(configuration: MergeConfiguration, contact):
    """Count objects for each field from given model with the target value."""
    objects_updated = {field: 0 for field in configuration.fields}

    for field, filtered_objects in _get_objects_from_configuration(configuration, contact):
        objects_updated[field] = filtered_objects.count()

    return objects_updated

def _get_objects_from_configuration(configuration: MergeConfiguration, source: Contact):
    """Gets objects for each configured field."""
    print(configuration)

    for field in configuration.fields:
        yield field, configuration.model.objects.filter(**{field: source})

def is_contact_a_valid_merge_source(contact: Contact):
    """Checks if contact can be moved and returns fields not allowed for merging."""
    # First, check that there are no references to the contact from other objects
    # (other than via the fields specified in ALLOWED_RELATIONS_FOR_MERGING).
    relations = get_related_fields(Contact)

    disallowed_fields = []
    for relation in relations:
        if relation.remote_field not in ALLOWED_RELATIONS_FOR_MERGING:
            if getattr(contact, relation.name).count():
                disallowed_fields.append(relation.name)

    if disallowed_fields:
        return False, disallowed_fields

    # Then, check that the source contact itself doesn't have any references to other
    # contacts.
    self_referential_fields = get_self_referential_relations(Contact)
    for field in self_referential_fields:
        if getattr(contact, field.name):
            return False, [field.name]

    return True, []

def is_contact_a_valid_merge_target(contact: Contact):
    """
    Returns whether the specified contact is a valid merge target.

    This checks that the target contact isn't archived.
    """
    return not contact.archived
