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


def get_model_non_mapped_field_names(es_model):
    """Gets the names of fields that are not mapped or computed."""
    return (
        get_model_field_names(es_model)
        - es_model.MAPPINGS.keys()
        - es_model.COMPUTED_MAPPINGS.keys()
        - {'_document_type'}
    )


def serialise_mapping(mapping_dict):
    """Serialises a mapping as JSON."""
    return json.dumps(mapping_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
