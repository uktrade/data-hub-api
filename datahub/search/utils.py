import json
from typing import NamedTuple


from datahub.core.utils import StrEnum


class SortDirection(StrEnum):
    """A direction for sorting."""

    asc = 'asc'
    desc = 'desc'


class SearchOrdering(NamedTuple):
    """An ordering for a search (i.e. a sort field and direction)."""

    field: str
    direction: SortDirection = SortDirection.asc

    @property
    def is_descending(self):
        """Returns whether this is a descending sort."""
        return self.direction == SortDirection.desc


def get_model_fields(es_model):
    """Gets the field objects for an ES model."""
    return es_model._doc_type.mapping.properties._params['properties']


def get_model_field_names(es_model):
    """Gets the field names for an ES model."""
    return get_model_fields(es_model).keys()


def get_model_copy_to_target_field_names(es_model):
    """Gets the names of fields (for an ES model) that are copy-to targets."""
    fields = get_model_fields(es_model)

    copy_to_field_lists = [
        [prop.copy_to] if isinstance(prop.copy_to, str) else prop.copy_to
        for prop in fields.values()
        if hasattr(prop, 'copy_to')
    ]

    return {field for fields in copy_to_field_lists for field in fields}


def get_model_non_mapped_field_names(es_model):
    """Gets the names of fields that are not copied to, mapped or computed."""
    return (
        get_model_field_names(es_model)
        - get_model_copy_to_target_field_names(es_model)
        - es_model.MAPPINGS.keys()
        - es_model.COMPUTED_MAPPINGS.keys()
    )


def serialise_mapping(mapping_dict):
    """Serialises a mapping as JSON."""
    return json.dumps(mapping_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')


def get_unique_values_and_exclude_nulls_from_list(data):
    """
    :param data: a list of values
    :return: a list of none empty unique values
    """
    return list(
        filter(None, set(data)),
    )
